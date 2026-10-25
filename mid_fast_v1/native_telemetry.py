"""Client-side native telemetry. No deployment, prewarming, or game-server claims."""
import hashlib
import hmac
import time


def fingerprint(value, salt):
    """Run-scoped pseudonym; never export the salt or raw AWS identifiers."""
    return hmac.new(salt, value.encode('utf-8'), hashlib.sha256).hexdigest()


def observe_invoke(client, runtime_arn, session_id, payload, salt, ordinal, clock=None):
    """Time one complete SDK invocation; retain cold calls and never retry here.

    The caller owns a single reused client and stable IDs per logical session.
    Raw responses belong only in private .local receipts. No error messages,
    request IDs, ARNs, or raw session IDs are copied into telemetry.
    """
    clock = clock or time.perf_counter_ns
    result = {
        'receiptSchemaVersion': 2,
        'measurementBoundary': 'external_sdk_full_response_not_game_server',
        'sessionFingerprint': fingerprint(session_id, salt),
        'sessionCallIndex': ordinal,
        'payloadSha256': hashlib.sha256(payload).hexdigest(),
        'requestStartedUnixNs': time.time_ns(),
        'complete': False, 'streamError': None, 'rawResponse': None,
        'headersMs': None, 'bodyAfterHeadersMs': None,
        'httpStatus': None, 'retryAttempts': None,
        'responseSessionMatches': None, 'streamCloseError': None,
    }
    stream = None
    start = clock()
    try:
        response = client.invoke_agent_runtime(
            agentRuntimeArn=runtime_arn, runtimeSessionId=session_id,
            qualifier='DEFAULT', contentType='application/json', payload=payload)
        result['headersMs'] = (clock() - start) / 1e6
        stream = response['response']
        metadata = response.get('ResponseMetadata', {})
        result['httpStatus'] = metadata.get('HTTPStatusCode')
        result['retryAttempts'] = metadata.get('RetryAttempts')
        returned = response.get('runtimeSessionId')
        result['responseSessionMatches'] = None if returned is None else returned == session_id
        body = stream.read()
        result['rawResponse'] = body.decode('utf-8')
        result['responseBytes'] = len(body)
        result['complete'] = True
    except Exception as error:
        result['streamError'] = type(error).__name__
        # Preserve status/retry evidence from botocore ClientError, not its text.
        details = getattr(error, 'response', {})
        metadata = details.get('ResponseMetadata', {}) if isinstance(details, dict) else {}
        for output, key in (('httpStatus', 'HTTPStatusCode'), ('retryAttempts', 'RetryAttempts')):
            if metadata.get(key) is not None:
                result[output] = metadata[key]
    finally:
        # Capture completion before cleanup: close() is not response latency.
        result['requestWallMs'] = (clock() - start) / 1e6
        result['requestCompletedUnixNs'] = time.time_ns()
        if result['headersMs'] is not None:
            result['bodyAfterHeadersMs'] = result['requestWallMs'] - result['headersMs']
        if stream is not None:
            try:
                stream.close()
            except Exception as error:
                result['streamCloseError'] = type(error).__name__
    return result


def session_diagnostics(receipts):
    """Audit observed client IDs, not unobserved server microVM lifecycles.

    Old receipts remain readable but cannot demonstrate session continuity.
    Only aggregate counts are returned; pseudonyms stay in private receipts.
    """
    fingerprints = {}
    owners = {}
    next_index = {}
    observed = 0
    issues = set()
    for row in receipts:
        token = row.get('sessionFingerprint')
        index = row.get('sessionCallIndex')
        if token is None and row.get('receiptSchemaVersion', 1) < 2:
            continue
        observed += 1
        key = row.get('sessionKey')
        if (not isinstance(token, str) or len(token) != 64
                or any(c not in '0123456789abcdef' for c in token)
                or not isinstance(key, str) or not key
                or type(index) is not int or index < 0):
            issues.add('invalid_session_telemetry')
            continue
        if key in fingerprints and fingerprints[key] != token:
            issues.add('session_changed_within_logical_session')
        if token in owners and owners[token] != key:
            issues.add('session_shared_between_logical_sessions')
        if index != next_index.get(key, 0) or index != row.get('sequence'):
            issues.add('session_call_index_mismatch')
        fingerprints[key] = token
        owners[token] = key
        next_index[key] = index + 1
        if row.get('responseSessionMatches') is False:
            issues.add('response_session_mismatch')
        retries = row.get('retryAttempts')
        if retries is not None and (type(retries) is not int or retries != 0):
            issues.add('unexpected_retry_metadata')
        status = row.get('httpStatus')
        if status is not None and (type(status) is not int or not 200 <= status < 300):
            issues.add('unsuccessful_http_status')
        if row.get('streamCloseError') is not None:
            issues.add('stream_cleanup_failed')
    if 0 < observed < len(receipts):
        issues.add('partial_session_telemetry')
    return {
        'status': 'not_recorded' if observed == 0 else 'observed',
        'observedCalls': observed, 'observedLogicalSessions': len(fingerprints),
        'issues': sorted(issues),
        'serverSessionLifecycleVerified': False,
    }


def gate_diagnostics(rows, full, deadline_ms, p95, p95_target, sessions):
    """Explain failures without changing the existing all-calls deadline gate."""
    first = [r for r in rows if r['firstInSession']]
    later = [r for r in rows if not r['firstInSession']]

    def counts(group):
        return {
            'count': len(group),
            'invalid': sum(bool(r['errors']) for r in group),
            'late': None if deadline_ms is None else sum(r['late'] is True for r in group),
        }

    reasons = []
    if not full:
        reasons.append('incomplete_or_reordered_plan')
    if any(r['errors'] for r in rows):
        reasons.append('invalid_or_incomplete_response')
    if deadline_ms is None:
        reasons.append('deadline_not_verified')
    else:
        if any(r['late'] for r in first):
            reasons.append('first_session_call_deadline_exceeded')
        if any(r['late'] for r in later):
            reasons.append('later_session_call_deadline_exceeded')
        if p95 is not None and p95 > p95_target:
            reasons.append('overall_p95_target_exceeded')
    reasons.extend(sessions['issues'])
    return {'failureReasons': reasons, 'firstCalls': counts(first),
            'laterCalls': counts(later), 'sessionTelemetry': sessions,
            'gameServerDeadlineVerified': False}
