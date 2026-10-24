import base64, json, urllib.error, urllib.request
B, PW, ok = 'http://127.0.0.1:5000', 'Password1!', []

def call(m, p, a=None, b=None):
    d = json.dumps(b).encode() if b is not None else None
    r = urllib.request.Request(B + p, data=d, method=m)
    r.add_header('Content-Type', 'application/json')
    if a:
        r.add_header('Authorization', 'Basic ' + base64.b64encode(
            ('%s:%s' % a).encode()).decode())
    try:
        with urllib.request.urlopen(r) as x:
            return x.status, json.loads(x.read() or b'{}')
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read() or b'{}')
        except ValueError:
            return e.code, {}

def tok(e):
    s, b = call('POST', '/api/user/gettoken', b={'email': e, 'password': PW})
    assert s == 200, (e, s, b)
    return (e, b['token'])

def ck(lbl, exp, s, b):
    ok.append(s == exp)
    print('%-4s %s/%s  %-40s %s' % ('PASS' if s == exp else 'FAIL', s, exp,
                                    lbl, (b.get('error') or '')[:60]))

W, K = tok('weiling@skipq.test'), tok('kumar@skipq.test')
A, M = tok('ahhock@skipq.test'), tok('meixiang@skipq.test')

s, b = call('GET', '/api/diner/stalls', W); ck('stall list', 200, s, b)
S = {x['stall_name']: x['id'] for x in b['stalls']}
h, mx = S['Ah Hock Chicken Rice'], S['Mei Xiang Laksa']
ck('bad stall id', 404, *call('GET', '/api/diner/stalls/bad/menu', W))
s, b = call('GET', '/api/diner/stalls/%s/menu' % h, W); ck('stall menu', 200, s, b)
so = next(i['id'] for i in b['items'] if not i['available'])
av = next(i['id'] for i in b['items'] if i['orderable'])

def order(st, it, q=1):
    return call('POST', '/api/diner/orders', W,
                {'stall_id': st, 'items': [{'item_id': it, 'quantity': q}]})

ck('closed stall', 409, *order(mx, av))
ck('sold-out item', 409, *order(h, so))
ck('empty basket', 409, *call('POST', '/api/diner/orders', W,
                              {'stall_id': h, 'items': []}))
ck('quantity 0', 400, *order(h, av, 0))

s, b = order(h, av, 2); ck('place order', 201, s, b)
P, V = '/api/diner/orders/' + b['id'], '/api/vendor/orders/%s/status' % b['id']

ck('SCOPE other diner', 403, *call('GET', P, K))
ck('owner reads it', 200, *call('GET', P, W))
ck('pay', 201, *call('POST', P + '/pay', W, {'method': 'PayNow'}))
ck('pay twice', 409, *call('POST', P + '/pay', W, {'method': 'PayNow'}))
ck('bad method', 400, *call('POST', P + '/pay', W, {'method': 'Bitcoin'}))

ck('SCOPE other stall', 403, *call('PATCH', V, M, {'status': 'PendingPreparation'}))
ck('GUARD skip ahead', 409, *call('PATCH', V, A, {'status': 'Collected'}))
ck('reject, no reason', 400, *call('PATCH', V, A, {'status': 'Rejected'}))
ck('GUARD allowed', 200, *call('PATCH', V, A, {'status': 'PendingPreparation'}))
ck('mark ready', 200, *call('PATCH', V, A, {'status': 'PendingCollection'}))
ck('no-show too early', 409, *call('PATCH', V, A, {'status': 'NoShow'}))

ck('price below zero', 400, *call('POST', '/api/vendor/menu', A,
                                  {'name': 'Test', 'price': -3}))
ck('SCOPE other menu', 403, *call(
    'PATCH', '/api/vendor/menu/%s/availability' % so, M, {'available': True}))
ck('dashboard', 200, *call('GET', '/api/vendor/dashboard', A))
ck('notifications', 200, *call('GET', '/api/diner/notifications', W))

print('\n%d/%d passed' % (sum(ok), len(ok)))
