"""One-off: sync NDI backend block from BINA into Pictures views.py."""
from pathlib import Path

pictures = Path(r"C:\Users\DELL\Pictures\New folder\ECSS\proponent\views.py")
bina = Path(r"C:\Users\DELL\Desktop\BINA\PERSONAL\ecss\proponent\views.py")

p_lines = pictures.read_text(encoding="utf-8").splitlines(keepends=True)
b_lines = bina.read_text(encoding="utf-8").splitlines(keepends=True)


def slice_b(start, end):
    return b_lines[start - 1 : end]


def find_line(prefix, lines, start=0):
    for i, line in enumerate(lines[start:], start):
        if line.startswith(prefix):
            return i
    raise ValueError(f"not found: {prefix!r}")


start_p = find_line("def proof_request(request):", p_lines)
end_p = find_line("def proof_request_employee", p_lines, start_p + 1)
start_e = find_line("def proof_request_employee", p_lines)
end_e = find_line("def fetch_relationship_data", p_lines, start_e + 1)
start_pp = find_line("def proof_request_proponent", p_lines)
start_fetch = find_line("from django.views.decorators.http import require_GET", p_lines)
end_webhook = find_line("def ndi_dash(request):", p_lines)

subscribe_fn = '''def _ndi_subscribe_thread(thread_id):
    """Tell NDI to deliver proofs for this thread to our registered webhook."""
    if not thread_id:
        return None
    webhook_id = getattr(settings, 'NDI_WEBHOOK_ID', 'ecssserverid')
    public_url = getattr(settings, 'NDI_WEBHOOK_PUBLIC_URL', '') or '(not set in settings)'
    BASE_URL = 'https://demo-client.bhutanndi.com/webhook/v1/subscribe/'
    token = get_access_token_ndi()
    post_data = {'webhookId': webhook_id, 'threadId': thread_id}
    try:
        res = requests.post(
            BASE_URL,
            json=post_data,
            headers={'Authorization': f'Bearer {token}'},
            verify=False,
            timeout=15,
        )
        res.raise_for_status()
        data = res.json()
        print(
            f'NDI subscribe OK thread={thread_id} webhookId={webhook_id} '
            f'registeredURL_hint={public_url} response={data}'
        )
        return data
    except Exception as e:
        print(f'NDI subscribe FAILED thread={thread_id} webhookId={webhook_id}: {e}')
        return None


'''

ndi_block = "".join(slice_b(1618, 1862))
ndi_block = subscribe_fn + ndi_block
ndi_block = ndi_block.replace(
    "    response_data['ndi_mobile_show_qr_also'] = getattr(settings, 'NDI_MOBILE_SHOW_QR_ALSO', True)\n    return response_data\n",
    "    response_data['ndi_mobile_show_qr_also'] = getattr(settings, 'NDI_MOBILE_SHOW_QR_ALSO', True)\n    _ndi_subscribe_thread(thread_id)\n    return response_data\n",
)

extra_views = '''

def _ndi_webhook_auth_ok(request):
    expected = (getattr(settings, 'NDI_WEBHOOK_AUTH_TOKEN', '') or '').strip()
    if not expected:
        return True
    auth = request.META.get('HTTP_AUTHORIZATION', '')
    return auth == f'Bearer {expected}' or auth == expected


@csrf_exempt
def ndi_webhook_ping(request):
    """Hit via ngrok to confirm NDI can reach your server."""
    print(f'ndi_webhook_ping {request.method} from {request.META.get("REMOTE_ADDR")}')
    if request.method == 'POST':
        print(request.body.decode('utf-8', errors='replace')[:2000])
    return JsonResponse({'statusCode': '202', 'statusDescription': 'Accepted'}, status=202)


@require_GET
def ndi_webhook_status(request):
    return JsonResponse({
        'webhookId': getattr(settings, 'NDI_WEBHOOK_ID', 'ecssserverid'),
        'NDI_WEBHOOK_PUBLIC_URL': getattr(settings, 'NDI_WEBHOOK_PUBLIC_URL', ''),
        'subscribeOnProofRequest': True,
        'pingUrl': '/ndi_webhook_ping/',
    })


@require_GET
def ndi_register_webhook(request):
    """Re-register webhook URL with NDI after ngrok URL changes."""
    public_url = (getattr(settings, 'NDI_WEBHOOK_PUBLIC_URL', '') or '').strip()
    if not public_url:
        return JsonResponse({'error': 'Set NDI_WEBHOOK_PUBLIC_URL to https://YOUR-NGROK/webhook/'}, status=400)
    webhook_id = getattr(settings, 'NDI_WEBHOOK_ID', 'ecssserverid')
    token = get_access_token_ndi()
    register_url = 'https://demo-client.bhutanndi.com/webhook/v1/register'
    body = {'webhookId': webhook_id, 'webhookURL': public_url}
    auth_token = (getattr(settings, 'NDI_WEBHOOK_AUTH_TOKEN', '') or '').strip()
    if auth_token:
        body['authType'] = 'oauth2'
        body['authVersion'] = 'v2'
        body['authToken'] = auth_token
    try:
        res = requests.post(
            register_url,
            json=body,
            headers={'Authorization': f'Bearer {token}'},
            verify=False,
            timeout=15,
        )
        res.raise_for_status()
        return JsonResponse({'ok': True, 'request': body, 'response': res.json()})
    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e), 'request': body}, status=500)

'''

ndi_block = ndi_block.replace(
    'def webhook(request):\n    print("Inside Webhook")\n    try:',
    'def webhook(request):\n    print("Inside Webhook")\n    if not _ndi_webhook_auth_ok(request):\n        print("NDI webhook auth mismatch (set NDI_WEBHOOK_AUTH_TOKEN if using OAuth2 v2)")\n        return JsonResponse({"statusCode": "401", "statusDescription": "Unauthorized"}, status=401)\n    try:',
)
ndi_block += extra_views

out = (
    p_lines[:start_p]
    + slice_b(1346, 1437)
    + p_lines[end_p:start_e]
    + slice_b(1440, 1489)
    + p_lines[end_e:start_pp]
    + slice_b(1538, 1609)
    + [ndi_block]
    + p_lines[end_webhook:]
)
pictures.write_text("".join(out), encoding="utf-8")
print("OK patched", pictures)
