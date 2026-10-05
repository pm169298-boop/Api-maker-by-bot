#!/usr/bin/env python3
r"""PRIVATE CONFIGURED app.py / main.py — SR DARK 4.17.0.
Contains existing credentials. Keep private. Start: python app.py.

# SR DARK v4.17.0 — simple customer bot

Private configured release. Developer: @DroidDeveloper.

## Customer menu

API Store | My APIs
Buy Credits | Wallet
Invite & Earn | Help

Admins additionally see Admin and Admin Panel. Free starter and short demo remain inside API Store, not as extra home-screen rows. Usage and redeem are inside Wallet. No new pack prices or exchange rates were invented.

## Removed from customer workflows

- Custom API creation, custom source editing and their direct callback/backend bypasses. Customers purchase owner-managed catalogue APIs instead.
- General support conversation, history/inbox screens and owner-purchase-inquiry flow. Old callbacks cannot revive them. Old encrypted history is retained but not exposed; pending unsent support screens are cancelled. Already in-flight requests cannot be recalled.
- The cluttered Buy/owner-preview journey. Buy Credits now shows the existing enabled coin pack amounts and Stars prices, with one Buy button per pack. Up to six packs per page.

A minimal /paysupport direct contact remains for payment/refund problems only, as referenced in invoices. It does not create a support thread or send an inquiry to the owner. It is not a home/menu support feature. Required billing support contact settings are preserved so Stars purchases are not broken.

## Payments and preservation

Clicking Buy produces a Telegram Stars invoice. It does not credit the wallet. The selected amount/price is validated against the current pack. Only a validated successful payment credits the wallet; duplicate payment/update protection remains. Buy Credits does not invent rupee payments or a Stars/diamond exchange rate.

Existing API keys, endpoints, usage, expiry, balances, orders, prices, header/query authentication policy and private CONFIG values are unchanged. Existing custom APIs continue serving; customers can no longer create new custom sources or rewrite existing custom data/upstreams. Admin source creation and management remain available.

Normal buttons edit the current screen. The previous typed /start or /admin recovery and durable offline/retry handling remain. No welcome sticker was added. New simple welcome screens use text; existing saved media is not deleted and explicit admin previews remain available.

## Deploy

Replace your running app.py with the configured app.py supplied for this release. Requirements are unchanged.

Build: pip install -r requirements.txt
Start: python app.py

main.py is an identical compatibility entrypoint if that is your hosting filename. Run one entrypoint, not both. No ENV values need to be entered for the existing configured deployment.

After deployment, /health must report version 4.17.0 and build PRIVATE-SIMPLE-417 with ok=true. Then use /start. The simple UI migration applies once, keeps the same Firebase namespace and does not reset data or rotate keys. Do not clear pending Telegram updates.

These files contain existing server credentials. Keep them private and out of public/static hosting or public repositories. Bundled rules are not automatically published. This release was not deployed by the assistant, and no production state write, invoice or message was sent in testing.

## Checks

786 automated tests passed: 767 compatibility/recovery/security/payment tests and 19 simple-mode tests. Local browser/webhook scenario passed for six-button home, priced credit purchase, invoice creation without premature credit, custom/support removal, admin approval, mobile layout and zero page JavaScript errors. Telegram/provider transports were mocked. Isolated Gunicorn startup/worker smoke passed. A separate no-ENV private initialization probe verifies configured Firebase REST and login availability with all networking and background threads blocked; it is not a real browser login or live-deployment verification.

"""
from __future__ import annotations

def firebase_rules(backend_uid,namespace='srdark_v4'):
    """Generate least-privilege client rules; no credentials or public grants."""
    import re as _re
    if not isinstance(backend_uid,str) or not _re.fullmatch(r'[A-Za-z0-9_-]{1,128}',backend_uid) or backend_uid.startswith(('REPLACE_','PASTE_')):
        raise ValueError('Fill the actual FIREBASE_BACKEND_UID first; no password belongs in rules.')
    if not isinstance(namespace,str) or not _re.fullmatch(r'[A-Za-z0-9_-]{1,50}',namespace):raise ValueError('Invalid FIREBASE_NAMESPACE.')
    allow="auth != null && auth.uid === '"+backend_uid+"' && auth.token.firebase.sign_in_provider === 'password'"
    return {'rules':{'.read':False,'.write':False,namespace:{
        'state':{'.read':allow,'.write':allow,'.validate':'newData.isString()'},
        'backups':{'.read':allow,'.write':allow,'$backup':{'.validate':"newData.hasChildren(['t','encrypted']) && newData.child('t').isNumber() && newData.child('encrypted').isString()"}}}}}

if __name__=='__main__' and '--print-firebase-rules' in __import__('sys').argv:
    import ast as _ast,json as _json,os as _os,sys as _sys
    from pathlib import Path as _Path
    _tree=_ast.parse(_Path(__file__).read_text())
    _config=next(n for n in _tree.body if isinstance(n,_ast.Assign) and any(isinstance(t,_ast.Name) and t.id=='CONFIG' for t in n.targets))
    _values=_ast.literal_eval(_config.value)
    try:
        _rules=firebase_rules(_os.environ.get('FIREBASE_BACKEND_UID',_values.get('FIREBASE_BACKEND_UID','')),_os.environ.get('FIREBASE_NAMESPACE',_values.get('FIREBASE_NAMESPACE','srdark_v4')))
    except ValueError as _error:
        print(str(_error),file=_sys.stderr);raise SystemExit(2)
    print(_json.dumps(_rules,indent=2));raise SystemExit(0)

# Dependency export works before third-party imports; no automatic installation.
RUNTIME_REQUIREMENTS = 'Flask==3.1.3\ngunicorn==26.2.0\nrequests==2.33.0\nurllib3==2.7.0\ncryptography==50.0.2\nfirebase-admin==7.7.0\nboto3==1.43.106\nredis==7.4.1\ntzdata==2026.4\n'
if __name__ == "__main__":
    import sys as _sys
    if "--print-requirements" in _sys.argv:
        print(RUNTIME_REQUIREMENTS, end="")
        raise SystemExit(0)

import argparse, base64, copy, hashlib, hmac, io, ipaddress, json, logging
import os, re, secrets, socket, sqlite3, sys, threading, time, urllib.parse, uuid, math
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from pathlib import Path
from functools import wraps
from contextlib import contextmanager
import requests
import urllib3
from cryptography.fernet import Fernet, InvalidToken
from flask import Flask, request, jsonify, session, render_template_string, redirect, send_file, has_request_context, g
from werkzeug.exceptions import HTTPException
from flask.json.provider import DefaultJSONProvider

# OPTIONAL ENV: fill these values directly for a private, server-only deployment.
CONFIG = {
    "BOOTSTRAP_V4171_CHAT_URLS": True,'BOOTSTRAP_V4151_EMOJI': True,
 'BOOTSTRAP_V415_CONTROLS': True,
 'AUTO_WORKER': True,
 'LOCK_OWNER_CONFIG': True,
 'PROXY_KEEPALIVE': True,
 'BOOTSTRAP_V414_SAFE_DELIVERY': True,
 'BOOTSTRAP_DASHBOARD_WELCOME': True,
 'BOOTSTRAP_VALIDATION_SOURCES': True,
 'TELEGRAM_WEBHOOK_CONNECTIONS': 4,
 'FIREBASE_ALLOW_SHARED_ACCOUNT': True,
 'FIREBASE_ACCESS_MODE': 'rest',
 'FIREBASE_BACKEND_EMAIL': 'Droid@gmail.com',
 'FIREBASE_BACKEND_PASSWORD': 'Droid0602',
 'FIREBASE_BACKEND_UID': '1egET0mDQXSXj2u5ZZxgxZlW3vd2',
 'BOT_TOKEN': '8351652662:AAE9kOGIU4m4QrJ7ixyc8n_4HpxDhY-KJ0s',
 'BOT_USERNAME': 'SR_free_api_bot',
 'SUPER_ADMIN_IDS': '8987478830',
 'BASE_URL': 'https://api-maker-by-bot.onrender.com',
 'SECRET_KEY': 'e7f5_cRfQ2CnMF4-pSuRBw4BzZfOnSD-IrfEIBzHFzad8_RA3l1g_EofHQcL4LKU',
 'WEBHOOK_SECRET': 'FC-LGiosyjGNkGqif0RM62wWfSpQHg2Oo0qfoip9FKVtQ1A4YDjK2VwY35YSn1Ds',
 'CRON_SECRET': 'GUUCUEN7PJ6MajZDLJzzON4LwUo-vW1BBSL0zU3WGoe-1gcDAuispkz58otXe-87',
 'FIREBASE_PROJECT_ID': 'vps-bot-api-makerbckup',
 'FIREBASE_WEB_CONFIG': {'apiKey': 'AIzaSyAlibQoi962M_JrsP-iVKHHl6K2bSbj8S4',
                         'authDomain': 'vps-bot-api-makerbckup.firebaseapp.com',
                         'databaseURL': 'https://vps-bot-api-makerbckup-default-rtdb.asia-southeast1.firebasedatabase.app',
                         'projectId': 'vps-bot-api-makerbckup',
                         'storageBucket': 'vps-bot-api-makerbckup.firebasestorage.app',
                         'messagingSenderId': '302260354275',
                         'appId': '1:302260354275:web:ae0ad26df6f5154f7419d6',
                         'measurementId': 'G-5Y0LEE2HPJ'},
 'INITIAL_LOG_CHANNEL': '-1004358894107',
 'FIREBASE_DATABASE_URL': 'https://vps-bot-api-makerbckup-default-rtdb.asia-southeast1.firebasedatabase.app',
 'FIREBASE_WEB_API_KEY': 'AIzaSyAlibQoi962M_JrsP-iVKHHl6K2bSbj8S4',
 'FIREBASE_SUPER_ADMIN_UIDS': '1egET0mDQXSXj2u5ZZxgxZlW3vd2',
 'FIREBASE_ADMIN_UIDS': '',
 'FIREBASE_SERVICE_ACCOUNT': '/etc/secrets/firebase-service-account.json',
 'FIREBASE_NAMESPACE': 'srdark_v4',
 'SQLITE_PATH': 'data/srdark.sqlite3',
 'S3_BUCKET': '',
 'S3_ENDPOINT_URL': '',
 'S3_REGION': 'auto',
 'S3_ACCESS_KEY': '',
 'S3_SECRET_KEY': '',
 'BACKUP_DIR': 'data/backups',
 'BACKUP_KEY': 'YQMBxEzc6rMCsaaPv4KwVI9CI_bbKY5PFRHR6CGm7to=',
 'HTTP_API_RPM': 180,
 'HTTP_GLOBAL_RPM': 1200,
 'TRUST_PROXY_HOPS': 0,
 'REDIS_URL': '',
 'REDIS_PREFIX': 'srdark-v4',
 'EXTRA_HOSTS': '',
 'BOOTSTRAP_V416_FOCUSED_UI': True,
 'BOOTSTRAP_V417_SIMPLE_UI': True}
def cfg(k):
    if k in ("SUPER_ADMIN_IDS","FIREBASE_SUPER_ADMIN_UIDS") and CONFIG.get("LOCK_OWNER_CONFIG") is True:return CONFIG.get(k,"")
    value=os.environ.get(k, CONFIG.get(k, ""))
    if k=='BASE_URL' and not value:value=os.environ.get('RENDER_EXTERNAL_URL','').rstrip('/')
    return value
DEMO = "--demo" in sys.argv or os.environ.get("SRD_DEMO") == "1"
VERSION = "4.17.1"
LOG = logging.getLogger("srdark")
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
SUPER_IDS = {x.strip() for x in str(cfg("SUPER_ADMIN_IDS")).split(",") if x.strip().isdigit()}
FB_SUPER_UIDS={x.strip() for x in str(cfg("FIREBASE_SUPER_ADMIN_UIDS")).split(",") if x.strip()}
FB_ADMIN_UIDS={x.strip() for x in str(cfg("FIREBASE_ADMIN_UIDS")).split(",") if x.strip()}
if DEMO:
    SUPER_IDS = {"10001"}
DEFAULTS = {
    "chat_keyed_receipts": False,
    "simple_customer_ui": False,
    "modern_controls": False, "key_style": "legacy", "safe_chat_receipts": False, "owner_approval_required": False, "web_unlock_minutes": 5,
    "starter_enabled": False, "starter_days": 10, "starter_daily": 100, "starter_rpm": 30,
    "starter_extend_price": 50, "starter_extend_days": 1, "starter_quota_price": 50, "starter_quota_add": 100, "custom_key_price": 50,

    "trial_enabled": True, "trial_minutes": 20, "trial_requests": 100, "trial_rpm": 30,
    "developer_username": "DroidDeveloper",
    "bot_user_rpm": 45, "bot_admin_rpm": 90, "focused_bot_ui": False, "supplied_emoji_enabled": False, "force_join_channels": [], "log_channel": str(cfg("INITIAL_LOG_CHANNEL") or "").strip(), "heartbeat_minutes": 60, "daily_report_hour": 0,
    "quota_warn_percent": 80, "button_icons": {}, "referral_new_user_reward": 50,
    "welcome_mode": "plain", "welcome_entities": [],
    "welcome_sticker": "", "welcome_sticker_info": {}, "bot_text_style": "compact",
    "welcome_photo": "", "welcome_caption": "💙 Welcome",
    "welcome_links": [], "campaigns_enabled": False, "campaign_timezone": "Asia/Kolkata",
    "delivery_start_hour": 10, "delivery_end_hour": 20, "campaign_daily_cap": 1, "campaign_gap_hours": 24,
    "default_api_price": 250, "referral_reward": 50, "diamond_coin_rate": 0,
    "purchase_packs": [], "support_username": "", "developer_name": "DROID", "developer_about": "SR DARK API platform",
    "api_receipts_txt": False, "admin_event_notifications": False, "default_header_only": False, "welcome_dashboard": False, "welcome_video": "", "developer_website": "", "payment_terms": "Virtual coins and diamonds are account-bound, have no cash value and cannot be withdrawn. Read the API plan before buying. Contact /paysupport for payment and refund assistance.", "daily_limit": 100, "valid_days": 10, "rpm": 30,
    "max_apis": 10, "max_payload_kb": 64, "referral_approval": False,
    "allow_custom": True, "allowed_hosts": [], "replace": [], "inject": {},
    "backup_hours": 6, "backup_keep": 8, "backup_delivery": "logs",
    "error_expired": "Your API has expired. Renew it using its configured wallet currency.",
    "error_daily": "Daily quota reached. Resets at 00:00 UTC.",
    "error_key": "A valid API key is required.",
}
def now(): return int(time.time())
def digest(s): return hashlib.sha256(str(s).encode()).hexdigest()
def new_id(prefix=""): return prefix + secrets.token_hex(8)
def iso(t): return datetime.fromtimestamp(t, timezone.utc).isoformat() if t else "Permanent"
def utc_day(): return datetime.fromtimestamp(now(),timezone.utc).strftime("%Y-%m-%d")
def validation_result(kind,value):
    # Stateless validation only: never contact UIDAI, a phone directory or a records provider.
    require(kind in ('phone_format','aadhaar_checksum'),'Unknown validation type.')
    raw=str(value).strip().replace(' ','').replace('-','')
    if kind=='phone_format':
        if raw.startswith('+91'):raw=raw[3:]
        return {'type':'number_format','country':'IN','format_valid':bool(re.fullmatch(r'[6-9][0-9]{9}',raw)),
                'subscriber_lookup':False,'identity_verified':False}
    valid=bool(re.fullmatch(r'[2-9][0-9]{11}',raw));checksum=False
    if valid:
        d=((0,1,2,3,4,5,6,7,8,9),(1,2,3,4,0,6,7,8,9,5),(2,3,4,0,1,7,8,9,5,6),(3,4,0,1,2,8,9,5,6,7),(4,0,1,2,3,9,5,6,7,8),
           (5,9,8,7,6,0,4,3,2,1),(6,5,9,8,7,1,0,4,3,2),(7,6,5,9,8,2,1,0,4,3),(8,7,6,5,9,3,2,1,0,4),(9,8,7,6,5,4,3,2,1,0))
        perm=((0,1,2,3,4,5,6,7,8,9),(1,5,7,6,2,8,3,0,9,4),(5,8,0,3,7,9,6,1,4,2),(8,9,1,6,0,4,3,5,2,7),
              (9,4,5,3,1,2,6,8,7,0),(4,2,8,6,5,7,3,9,0,1),(2,7,9,3,8,0,6,4,1,5),(7,0,4,6,9,1,3,2,5,8))
        check=0
        for i,digit in enumerate(reversed(raw)):check=d[check][perm[i%8][int(digit)]]
        checksum=check==0
    return {'type':'aadhaar_format_checksum','format_valid':valid,'checksum_valid':checksum,
            'identity_verified':False,'registry_lookup':False}

def bootstrap_validation_sources(state):
    flag=cfg('BOOTSTRAP_VALIDATION_SOURCES')
    if not (flag is True or isinstance(flag,str) and flag.lower() in ('true','1')) or state['system'].get('v412_validation_sources'):return
    for cid,name,kind,sample in (
        ('cat_validation_number','Number format validation','phone_format','0000000000'),
        ('cat_validation_aadhaar','Aadhaar format / checksum','aadhaar_checksum','000000000000')):
        state['catalog'].setdefault(cid,{'id':cid,'name':name,'mode':'validation','validator':kind,'param':'value','example_value':sample,
            'url':'','data':None,'enabled':True,'trial_enabled':True,'price':state['settings']['default_api_price'],'billing_currency':'coins',
            'demo_response':validation_result(kind,sample)})
    state['system']['v412_validation_sources']=True

def fresh():
    return {"schema": 4, "settings": copy.deepcopy(DEFAULTS), "users": {}, "apis": {},
            "catalog": {}, "campaigns": {}, "logs": {}, "kv": {}, "referrals": {}, "outbox": {},
            "support_threads": {}, "approvals": {}, "starter_claims": {}, "admin_notifications": {}, "redeem_codes": {}, "credit_grants": {}, "trial_claims": {}, "orders": {}, "charges": {}, "manual_refs": {}, "ledger": {}, "updates": {}, "login_codes": {}, "login_limits": {}, "sessions": {}, "challenges": {}, "system": {"v49_delivery_policy":True,"v411_minimal_welcome":True}}
def normalize(s):
    s = s or fresh()
    for k, v in fresh().items(): s.setdefault(k, copy.deepcopy(v))
    old=s["settings"]
    if not s['system'].get('v49_delivery_policy'):
        # One-time requested upgrade: subsequent owner customizations are preserved.
        old.update(backup_hours=6,backup_delivery='logs',campaign_daily_cap=1,campaign_gap_hours=24)
        s['system']['v49_delivery_policy']=True
    if not s['system'].get('v411_minimal_welcome'):
        # Owner-requested one-time minimal welcome; later explicit edits remain editable.
        old.update(welcome_caption='💙 Welcome',welcome_mode='plain',welcome_entities=[])
        s['system']['v411_minimal_welcome']=True
    if "default_api_price" not in old and "referral_cost" in old:
        old["default_api_price"]=int(old["referral_cost"])*50
    old.pop("referral_cost",None)
    for u in s['users'].values():
        if 'coins' not in u:u['coins']=int(u.get('credits',0))*50
        u.pop('credits',None);u.setdefault('diamonds',0);u.setdefault('wallet_hold',False)
        u.setdefault('updates_on',False);u.setdefault('telegram_started',str(u.get('id','')).isdigit())
        if 'broadcast_policy' not in u:
            # Ambiguous historical unsubscribed accounts are conservatively left alone.
            u['broadcast_hold']=bool(u.get('telegram_started') and not u.get('updates_on') or u.get('last_optout_reply'))
            u['broadcast_policy']='auto-start-v1'
        u.setdefault('last_active',u.get('joined',now()));u.setdefault('campaign_events',{})
        u['campaign_events']={k:({aid:mark for aid,mark in v.items() if aid in s['apis'] and s['apis'][aid].get('owner')==str(u.get('id',''))} if isinstance(v,dict) else v) for k,v in u['campaign_events'].items() if k in s['campaigns']}
        if u.get('promo_pending') not in s['outbox']:u['promo_pending']=''
    for r in s['referrals'].values():r.setdefault('reward',50);r.setdefault('new_user_reward',0)
    for a in s['apis'].values():
        a.setdefault('billing_currency','coins');a.setdefault('price',old.get('default_api_price',250))
    s["settings"] = {**DEFAULTS, **old}
    bootstrap_validation_sources(s)
    flag=cfg('BOOTSTRAP_DASHBOARD_WELCOME')
    if (flag is True or str(flag).lower() in ('1','true','yes')) and not s['system'].get('v413_dashboard'):
        s['settings'].update(welcome_dashboard=True,welcome_sticker='',welcome_sticker_info={})
        clear_welcome_stickers(s);s['system']['v413_dashboard']=True
    flag=cfg('BOOTSTRAP_V414_SAFE_DELIVERY')
    if (flag is True or str(flag).lower() in ('1','true','yes')) and not s['system'].get('v414_safe_delivery'):
        s['settings'].update(api_receipts_txt=True,admin_event_notifications=True)
        s['system']['v414_safe_delivery']=True
    flag=cfg('BOOTSTRAP_V415_CONTROLS')
    if (flag is True or str(flag).lower() in ('1','true','yes')) and not s['system'].get('v415_controls'):
        s['settings'].update(modern_controls=True,key_style='droid15',safe_chat_receipts=True,owner_approval_required=True,web_unlock_minutes=30,starter_enabled=True,default_header_only=True)
        for src in s['catalog'].values():src.setdefault('starter_enabled',bool(src.get('trial_enabled')))
        s['system']['v415_controls']=True
    flag=cfg('BOOTSTRAP_V4151_EMOJI')
    if (flag is True or str(flag).lower() in ('1','true','yes')) and not s['system'].get('v4151_supplied_emoji'):
        s['settings']['supplied_emoji_enabled']=True;s['system']['v4151_supplied_emoji']=True
    flag=cfg('BOOTSTRAP_V416_FOCUSED_UI')
    if (flag is True or str(flag).lower() in ('1','true','yes')) and not s['system'].get('v416_focused_ui'):
        s['settings']['focused_bot_ui']=True;s['system']['v416_focused_ui']=True
    flag=cfg('BOOTSTRAP_V417_SIMPLE_UI')
    if (flag is True or str(flag).lower() in ('1','true','yes')) and not s['system'].get('v417_simple_ui'):
        s['settings'].update(simple_customer_ui=True,focused_bot_ui=True,modern_controls=True,allow_custom=False)
        for u in s['users'].values():
            f=u.get('flow',{})
            if f.get('step') in ('support_chat','support_reply','owner_quote'):u['flow']={}
        for k,j in list(s['outbox'].items()):
            if j.get('support_private') and not j.get('lease',0)>now():del s['outbox'][k]
        s['system']['v417_simple_ui']=True
    flag=cfg('BOOTSTRAP_V4171_CHAT_URLS')
    if (flag is True or str(flag).lower() in ('1','true','yes')) and not s['system'].get('v4171_chat_urls'):
        s['settings'].update(chat_keyed_receipts=True,api_receipts_txt=False,safe_chat_receipts=True,default_header_only=False)
        for u in s['users'].values():u.pop('receipt_mode',None)
        s['system']['v4171_chat_urls']=True
    return s
class Problem(Exception):
    def __init__(self, message, status=400, code="INVALID_REQUEST"):
        super().__init__(message); self.message=message; self.status=status; self.code=code

def require(condition, message, status=400, code="INVALID_REQUEST"):
    if not condition: raise Problem(message, status, code)

def validate_json_tree(value, max_depth=32, max_nodes=20000):
    """Iterative shape validation: no recursive Python walk on untrusted input."""
    stack=[(value,0)]; count=0
    while stack:
        node,depth=stack.pop(); count+=1
        require(depth<=max_depth and count<=max_nodes,"JSON nesting/item limit exceeded.",400,"JSON_COMPLEXITY")
        if isinstance(node,dict):
            require(all(isinstance(k,str) for k in node),"JSON object keys must be strings.")
            require(count+len(stack)+len(node)<=max_nodes,"JSON item limit exceeded.",400,"JSON_COMPLEXITY")
            stack.extend((v,depth+1) for v in node.values())
        elif isinstance(node,list):
            require(count+len(stack)+len(node)<=max_nodes,"JSON item limit exceeded.",400,"JSON_COMPLEXITY")
            stack.extend((v,depth+1) for v in node)
        elif isinstance(node,float): require(math.isfinite(node),"Non-finite JSON numbers are not allowed.")
        else: require(node is None or isinstance(node,(str,int,bool)),"Unsupported JSON value.")
    return value

def reject_duplicate_keys(pairs):
    result={}
    for key,value in pairs:
        if key in result: raise ValueError("Duplicate JSON keys are not allowed.")
        result[key]=value
    return result

def reject_constant(value): raise ValueError("Non-finite JSON constants are not allowed.")
class StrictJSONProvider(DefaultJSONProvider):
    def loads(self,value,**kwargs):
        kwargs.setdefault("object_pairs_hook",reject_duplicate_keys)
        kwargs.setdefault("parse_constant",reject_constant)
        try: return json.loads(value,**kwargs)
        except RecursionError: raise ValueError("JSON nesting limit exceeded.")

def strict_json(value):
    try: result=json.loads(value,object_pairs_hook=reject_duplicate_keys,parse_constant=reject_constant)
    except (ValueError,RecursionError): raise Problem("Invalid JSON, duplicate keys, or excessive nesting.")
    return validate_json_tree(result)

def role(uid, s):
    uid=str(uid)
    if uid.startswith("fb:"):
        raw=uid[3:]
        return "superadmin" if raw in FB_SUPER_UIDS else "admin" if raw in FB_ADMIN_UIDS else "user"
    if uid in SUPER_IDS: return "superadmin"
    return "admin" if s["users"].get(str(uid), {}).get("role")=="admin" else "user"
def is_admin(uid, s): return role(uid, s) in ("admin", "superadmin")
def actor(s, uid, admin=False, superonly=False):
    if str(uid).startswith("fb:"):
        require(str(uid)[3:] in FB_SUPER_UIDS | FB_ADMIN_UIDS,"Firebase admin access is not approved or has been removed.",403)
    u=s["users"].get(str(uid))
    require(u is not None and not u.get("blocked"), "Account unavailable.", 403)
    require(not admin or is_admin(uid,s), "Admin access required.",403)
    require(not superonly or role(uid,s)=="superadmin", "Super-admin access required.",403)
    return u

def audit(s, uid, event, detail=""):
    k=new_id(); s["logs"][k]={"t":now(), "actor":str(uid), "event":event, "detail":str(detail)[:250]}
    if len(s["logs"])>400:
        for x in sorted(s["logs"],key=lambda k:s["logs"][k]["t"])[:-400]: del s["logs"][x]
    ops_audit(s,uid,event,detail)
    admin_event(s,uid,event,detail)

def md(s): return re.sub(r'([_*\[\]()~`>#+\-=|{}.!\\])', r'\\\1', str(s))
def code(s): return "`"+str(s).replace("\\","\\\\").replace("`","\\`")+"`"
def btn(text, callback=None, style="primary", url=None):
    require(bool(callback) != bool(url),'A button must have exactly one linked action.')
    if callback:require(isinstance(callback,str) and 1<=len(callback.encode())<=64,'Invalid button callback.')
    b={"text":text,"style":style}
    b["url" if url else "callback_data"] = url or callback
    return b

# Decorative Unicode is used only for fixed headings, never names, keys or URLs.
_SMALL_CAPS = str.maketrans('abcdefghijklmnopqrstuvwxyz', 'ᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘqʀꜱᴛᴜᴠᴡxʏᴢ')
def bot_title(s, title):
    value=title.lower().translate(_SMALL_CAPS) if s['settings'].get('bot_text_style')=='compact' else title
    return '*'+md(value)+'*'

def ready_url_buttons(result):
    value=result.get("ready_url","")
    # Telegram CopyTextButton supports up to 256 characters; longer URLs remain copyable code text.
    return [[{"text":"Copy full URL","copy_text":{"text":value},"style":"primary"}]] if 1<=len(value)<=256 else []

# Owner-supplied IDs. They are not a Premium entitlement or verified artwork catalogue.
CUSTOM_EMOJIS={
    'make_post':('💖','6336646834139700626'),'connect_channel':('🤙',None),'send_channel':('👏',None),
    'admin_panel':('🛠',None),'success':('✅','6336861449360514102'),'error':('👎','6337033209397649451'),
    'broadcast':('🚨','6336698133229082903'),'status':('🎚','6336674562448563935'),
    'welcome':('💙','6336756235546663929'),'bot_active':('🚀','6336835907190004485')}
PREMIUM_EMOJIS=tuple(dict.fromkeys("""
6100639476441161711 6102462664288509137 6100199534351097095 6102926404792360795 6100409966273764915 6100430105375415737 6102470558438400435 6100451820730064687 6102638599033858630 6100179369479642954 6100485115316542792 6102661242101440205 6102592514034770678 6102475626499808862 6102863908723236868 6102510630483271620
6282589525348720171 6055377380204092112 6055551219005398825 6055181976371994390 6055481009175010794 6055484548228062462 6055202102588742236 6055450347403484860 6055228576767155521 6055183995006623379
6337009415278828759 6336756235546663929 6334772471757020134 6336732269629153634 6336833407519038409 6337048276142924106 6337018975876030803 6336608132189395373 6336797785060286399 6336685231147326793 6336907611669011898 6336988189550451848 6337098578799893838 6336808092981796477 6337020083977592163 6337112997005107243 6337051755066433311 6336835907190004485 6336618976981818626 6336857218817728795 6336974471424908889 6337125748763008448 6337098338281725706 6336962978092425393 6336633214798404108 6337019139084786234 6337035356881296575 6337026908680625329 6336690569791676356 6337106906741480828 6337072645787361389 6336720729052027967 6336670885956557643 6337113894653271580 6334488003188105980 6336721798498884548 6336799284003873851 6337112129421713282 6336599202952388231 6336755629956275338 6334702021408465964 6337109865973948062 6336708763273142215 6337083451925078342 6336930400765484501 6334788126912815244 6337059606266651217 6336812005697002754 6336813629194640485 6337085796977221633 6336663202260065128 6334324468013341494 6337047855236129713 6336782885818742144 6336664645369076808 6336910583786383660 6336862179504954500 6336697226990985005 6336772620846899242 6337033209397649451 6336861449360514102 6336573617832206335 6337055242579876765 6336789422758960593 6336781331040577785 6336603218746810844 6337123072998383823 6336894825551371014 6334681658968513467 6336799919659031563 6336707603631972035 6336874467406389346 6336756411640323933 6336608037700115865 6336613247495445753 6336973539417007164 6336931040715612818 6336653869296132233 6336836572909938734 6336798231736885254 6336813951317187443 6336866435817545002 6336662845777780692 6336580455420141312 6336750437340816001 6336677470141422007 6337078718871117522 6336931345658289868 6336935322798005307 6336646834139700626 6337010179783007229 6336618208182673162 6336580975111184057 6336957184181543528 6336991256157101601 6336655355354815762 6336795865209904645 6337054177427988529 6336855354801921798 6336878444546105899 6336861037043654967 6336662472115626382 6337093386184432717 6336637947852365586 6336876696494417749 6334678278829252492 6337087411884923105 6336989731443711607 6336882614959349480 6336886055228153516 6336797591786757523 6336674519498890396 6336856849450540332 6337048379222138619 6336816932024491505 6336672814396874442 6336835035311644293 6336668004033504924 6336682357814205676 6336764563488252026 6337100812182887680 6336575056646249129
""".split()))

# Exact glyph-to-ID pairs verified through Telegram getCustomEmojiStickers; no per-reply lookup.
VERIFIED_SUPPLIED_EMOJI = {'💀': '6100639476441161711', '🐉': '6102462664288509137', '👽': '6100199534351097095', '🐢': '6102926404792360795', '👾': '6100409966273764915', '🦆': '6100430105375415737', '🐧': '6102470558438400435', '⚰️': '6100451820730064687', '🐼': '6102638599033858630', '🦦': '6100179369479642954', '🐰': '6100485115316542792', '🦊': '6102661242101440205', '🐒': '6102592514034770678', '🦉': '6102475626499808862', '🦝': '6102863908723236868', '🐺': '6102510630483271620', '🎁': '6282589525348720171', '🏆': '6055377380204092112', '✅': '6336861449360514102', '💙': '6336756235546663929', '🐾': '6334772471757020134', '🦋': '6336732269629153634', '🔝': '6337048276142924106', '🥸': '6337018975876030803', '🔩': '6336608132189395373', '⏬': '6336797785060286399', '⚡️': '6336685231147326793', '✨': '6336907611669011898', '❤️': '6336988189550451848', '💜': '6337098578799893838', '👻': '6336808092981796477', '♥️': '6337112997005107243', '👛': '6337051755066433311', '🚀': '6336835907190004485', '📍': '6336618976981818626', '⏫': '6336857218817728795', '🚨': '6336698133229082903', '🚫': '6337125748763008448', '🕊': '6336962978092425393', '🌙': '6336633214798404108', '🎸': '6337019139084786234', '🫀': '6337035356881296575', '‼️': '6337026908680625329', '🔘': '6336690569791676356', '⭐️': '6337106906741480828', '🛸': '6337072645787361389', '💤': '6336720729052027967', '🙏': '6334488003188105980', '🎮': '6336721798498884548', '🔇': '6337112129421713282', '🔥': '6336755629956275338', '💬': '6334702021408465964', '🆓': '6337109865973948062', '❓': '6336708763273142215', '💰': '6337083451925078342', '🧠': '6334788126912815244', '😐': '6337085796977221633', '💼': '6336663202260065128', '💡': '6334324468013341494', '🐈': '6337047855236129713', '🐍': '6336664645369076808', '🏴\u200d☠️': '6336697226990985005', '⚪️': '6336772620846899242', '👎': '6337033209397649451', '👣': '6336573617832206335', '🐋': '6337055242579876765', '⭕️': '6336781331040577785', '🎥': '6337123072998383823', '🤬': '6336894825551371014', '😂': '6336799919659031563', '🌟': '6336707603631972035', '🔐': '6336608037700115865', '⭐': '6336613247495445753', '🍏': '6336973539417007164', '⚡': '6336931040715612818', '⏩': '6336653869296132233', '🗿': '6336798231736885254', '🗑️': '6336662845777780692', '💍': '6336580455420141312', '😈': '6336750437340816001', '😎': '6336677470141422007', '😿': '6336935322798005307', '💖': '6336646834139700626', '😊': '6336618208182673162', '😀': '6336580975111184057', '🙂': '6336655355354815762', '🤣': '6336795865209904645', '💘': '6336855354801921798', '❤': '6336861037043654967', '💯': '6337093386184432717', '👍': '6336876696494417749', '🔗': '6334678278829252492', '🎄': '6336989731443711607', '😃': '6336886055228153516', '💎': '6336816932024491505', '❤️\u200d🔥': '6336835035311644293', '🐈\u200d⬛': '6336682357814205676', '⬜️': '6337100812182887680', '🎚': '6336674562448563935', '🩶': '6025929233291809651', '🤩': '6078087767106001151', '🔣': '6285315214673975495', '⚠️': '5420323339723881652', '❣️': '5352727529511723136', '☠️': '5253539825360843975', '🍼': '6226493198013830325'}

def supplied_emoji_active(s):
    return s['settings'].get('supplied_emoji_enabled',False) and s['system'].get('supplied_emoji_disabled_until',0)<=now()

def supplied_button_icon(button):
    action=str(button.get('callback_data','')).removeprefix('cmd:').split(':')[0]
    name='broadcast' if action.startswith(('broadcast','campaign')) else 'status' if action in ('mystats','adminstats','dashboard','stats','daily') else 'make_post' if action in ('create','buyapi','newstatic','newproxy','addsource','starter') else 'welcome' if action in ('home','start') else None
    if name:return CUSTOM_EMOJIS[name][1]
    return CUSTOM_EMOJIS['success' if button.get('style')=='success' else 'error' if button.get('style')=='danger' else 'welcome'][1]

def premium_entities(text,entities):
    # Never alter the text or randomly replace emoji graphemes; only add safe entity annotations.
    out=copy.deepcopy(entities);protected=[(e['offset'],e['offset']+e['length']) for e in entities if e['type'] in ('custom_emoji','code','pre','text_link','url','email','text_mention')]
    for match in re.finditer(r'(?:https?://|tg://|www\.)\S+',text):protected.append((text_units(text[:match.start()]),text_units(text[:match.end()])))
    mapping=VERIFIED_SUPPLIED_EMOJI
    for match in re.finditer('|'.join(re.escape(x) for x in sorted(mapping,key=len,reverse=True)),text):
        start,end=match.span();before=text[start-1:start];after=text[end:end+1]
        if before=='\u200d' or after in ('\u200d','\ufe0f','\u20e3') or after and 0x1f3fb<=ord(after)<=0x1f3ff:continue
        a=text_units(text[:start]);b=text_units(text[:end])
        if any(max(a,c)<min(b,d) for c,d in protected):continue
        if len(out)>=min(64,len(entities)+12):break
        out.append({'type':'custom_emoji','offset':a,'length':b-a,'custom_emoji_id':mapping[match[0]]})
    return rich_entities(text,out)

def premium_message_job(job):
    if not job.get('premium_emojis') or job.get('emoji_fallback') or job.get('format_fallback') or job.get('receipt'):return job
    try:
        text=job.get('text','');entities=job.get('entities',[])
        if not job.get('plain_text'):text,entities=parse_markdown(text,max_units=4096)
        decorated=premium_entities(text,entities)
        if decorated==entities:return job
        return {**job,'text':text,'plain_text':True,'entities':decorated}
    except (Problem,ValueError,TypeError):return job # Preserve existing formatting if it cannot be safely converted.

def enqueue(s, chat, text, keyboard=None, kind="message", backup=None):
    auto_icons=[];premium=supplied_emoji_active(s)
    if keyboard:
        keyboard=copy.deepcopy(keyboard)
        for ri,row in enumerate(keyboard):
            for bi,button in enumerate(row):
                require(sum(bool(button.get(k)) for k in ('callback_data','url','copy_text'))==1,'Button must have exactly one callback, link or copy action.')
                icon=s['settings'].get('button_icons',{}).get(button.get('style','primary'))
                if icon:button['icon_custom_emoji_id']=icon
                elif premium and not button.get('icon_custom_emoji_id'):
                    button['icon_custom_emoji_id']=supplied_button_icon(button);auto_icons.append([ri,bi])
    key=new_id(); s["outbox"][key]={"chat":str(chat),"text":text,"keyboard":keyboard,
        "kind":kind,"backup":backup,"t":now(),"tries":0,"next":0,"lease":0}
    if focused_ui(s) and kind=='message' and any(marker in text for marker in ('Secure panel login','Sensitive action confirmation','GIFT_','Referral qualified','Welcome reward','Payment received','Refund processed')):s['outbox'][key]['receipt']=True
    if premium and kind in ('message','photo','engagement','opslog','admin_event','approval'):s['outbox'][key]['premium_emojis']=True
    if auto_icons:s['outbox'][key]['auto_emoji_buttons']=auto_icons
    # No silent dropping: stop accepting business writes if delivery backlog is excessive.
    require(len(s["outbox"])<=2000,"Notification backlog full; admin must run the scheduler.",503)
    return key
def chat_url_credentials(a,result,title):
    # Telegram text/entities, not HTML: ampersands stay literal and secrets stay in code entities.
    text='';entities=[]
    def add(value,kind=None):
        nonlocal text
        value=str(value);offset=text_units(text);text+=value
        if kind:entities.append({'type':kind,'offset':offset,'length':text_units(value)})
    icon='⏱' if a.get('is_trial') else '🎁' if a.get('is_starter') else '🔑'
    add(icon+' '+title,'bold');add('\n\n'+a['name']+'\nExpires: '+iso(a['expires']))
    if a.get('is_trial'):add('\nTotal request budget: '+str(a['trial_limit']))
    else:add('\nLimits: '+str(a['daily'])+'/day · '+str(a['rpm'])+'/minute')
    add('\n\n');add('Request URL — header required' if a.get('header_only') else 'Ready JSON URL','bold');add('\n')
    add(result['request_url'] if a.get('header_only') else result['ready_url'],'code')
    if a.get('header_only'):
        add('\n\n');add('Authentication','bold');add('\n');add('X-API-Key: '+result['key'],'code')
    add('\n\nKeep this key and URL private.')
    if a.get('is_trial'):add(' Trial time and budget do not restart.')
    require(text_units(text)<=4000,'Credential message is too long; shorten the public example value.',409)
    return {'text':text,'entities':entities}

def enqueue_api_receipt(s,uid,result,title):
    require(str(uid).isdigit() and bool(result.get('credential_text')),'Private Telegram receipt unavailable.')
    aid=result['id'];a=s['apis'].get(aid);require(a and (a['owner']==str(uid) or is_admin(uid,s)),'Receipt access denied.',403)
    mode=credential_delivery_mode(s,uid)
    linked=mode=='text' and s['settings'].get('chat_keyed_receipts',False)
    plaintext=json.dumps(chat_url_credentials(a,result,title),ensure_ascii=False) if linked else safe_chat_credentials(result) if mode=='text' else result['credential_text']
    key=enqueue(s,uid,title+(' — private credential text.' if mode=='text' else ' — credentials are in the private TXT attachment.'),[[btn('My APIs','apis'),btn('Home','home')]],kind='api_receipt')
    s['outbox'][key].update(receipt_enc=fernet().encrypt(plaintext.encode()).decode(),receipt_format='chat_url' if linked else mode,receipt_api_id=aid,
        receipt_key_hash=digest(result['key']),filename=aid+'.txt',priority=-30 if linked else -2)
    return key

def notify_admins(s, text, superonly=False):
    ids=set(SUPER_IDS)
    if not superonly: ids.update(k for k,u in s["users"].items() if k.isdigit() and u.get("role")=="admin" and not u.get("blocked"))
    for uid in ids: enqueue(s,uid,text)

# Direct Firebase Auth + RTDB REST. HTTPS Google endpoints validate every login token.
# Passwords/refresh tokens are private process memory; never state, browser output or logs.
_OUTBOUND_LOCAL=threading.local()
def outbound_http(method,url,**kwargs):
    # One keep-alive pool per process/thread; credentials stay request-scoped.
    # Explicitly no automatic retries: uncertain writes/sends must not be replayed.
    pid=os.getpid()
    if getattr(_OUTBOUND_LOCAL,'pid',None)!=pid or not getattr(_OUTBOUND_LOCAL,'client',None):
        old=getattr(_OUTBOUND_LOCAL,'client',None)
        if old:old.close()
        client=requests.Session()
        adapter=requests.adapters.HTTPAdapter(pool_connections=4,pool_maxsize=4,max_retries=0,pool_block=True)
        client.mount('https://',adapter)
        _OUTBOUND_LOCAL.client=client;_OUTBOUND_LOCAL.pid=pid
    return _OUTBOUND_LOCAL.client.request(method,url,**kwargs)

def firebase_http(method,url,*,params=None,payload=None,form=None,headers=None,limit=32*1024*1024):
    try:
        with outbound_http(method,url,params=params,json=payload if form is None else None,data=form,
                              headers=headers or {},timeout=(3,10),allow_redirects=False,stream=True) as response:
            raw=bytearray()
            for block in response.iter_content(65536):
                raw.extend(block)
                require(len(raw)<=limit,'Firebase response exceeded its safety limit.',503,'FIREBASE_RESPONSE_SIZE')
            try:data=json.loads(raw.decode('utf-8'),object_pairs_hook=reject_duplicate_keys,parse_constant=reject_constant) if raw else None
            except (ValueError,UnicodeError,RecursionError):raise Problem('Firebase returned an invalid response.',503,'FIREBASE_PROTOCOL') from None
            return response.status_code,data,dict(response.headers)
    except Problem:raise
    except Exception:raise Problem('Firebase connection failed. Retry after checking service availability.',503,'FIREBASE_UNAVAILABLE') from None

def firebase_identity(operation,data):
    require(operation in ('signInWithPassword','lookup','refresh'),'Unsupported Firebase Auth operation.')
    key=str(cfg('FIREBASE_WEB_API_KEY'));require(key,'Set the Firebase public Web API key.',503)
    if operation=='refresh':
        url='https://securetoken.googleapis.com/v1/token'
        status,result,_=firebase_http('POST',url,params={'key':key},form=data,limit=65536)
    else:
        url='https://identitytoolkit.googleapis.com/v1/accounts:'+operation
        status,result,_=firebase_http('POST',url,params={'key':key},payload=data,limit=65536)
    if status>=500 or status==429:raise Problem('Firebase authentication is temporarily unavailable.',503,'FIREBASE_UNAVAILABLE')
    require(status==200 and isinstance(result,dict),'Firebase authentication rejected. Check the account, password and Email/Password provider.',401,'FIREBASE_AUTH_FAILED')
    return result

def firebase_rest_verify(id_token,expected_uid=None):
    require(isinstance(id_token,str) and 100<=len(id_token)<=8192,'Invalid Firebase ID token.',401)
    # Do not use decoded JWT claims to authenticate: first require Google's authenticated lookup.
    result=firebase_identity('lookup',{'idToken':id_token})
    users=result.get('users',[])
    require(isinstance(users,list) and len(users)==1 and isinstance(users[0],dict),'Firebase account could not be verified.',401,'FIREBASE_AUTH_FAILED')
    user=users[0];uid=user.get('localId')
    require(isinstance(uid,str) and re.fullmatch(r'[A-Za-z0-9_-]{1,128}',uid),'Invalid Firebase account identifier.',401)
    try:
        parts=id_token.split('.');require(len(parts)==3 and bool(parts[2]),'Invalid Firebase token.',401)
        def decode(part):
            require(re.fullmatch(r'[A-Za-z0-9_-]+',part),'Invalid Firebase token encoding.',401)
            return strict_json(base64.urlsafe_b64decode(part+'='*((4-len(part)%4)%4)).decode())
        header=decode(parts[0]);claims=decode(parts[1])
        require(isinstance(header,dict) and header.get('alg')=='RS256' and isinstance(claims,dict),'Invalid Firebase token format.',401)
        project=str(cfg('FIREBASE_PROJECT_ID'))
        require(project and claims.get('aud')==project and claims.get('iss')=='https://securetoken.google.com/'+project,
                'Firebase token belongs to a different project.',401,'FIREBASE_PROJECT_MISMATCH')
        require(claims.get('sub')==uid and (expected_uid is None or uid==expected_uid),'Firebase account mismatch.',401,'FIREBASE_ACCOUNT_MISMATCH')
        require(all(type(claims.get(k)) is int for k in ('iat','exp','auth_time')),'Invalid Firebase token times.',401)
        require(0<claims['auth_time']<=now()+30 and 0<claims['iat']<=now()+30 and claims['exp']>now(), 'Firebase token expired or not yet valid.',401)
        require(isinstance(claims.get('firebase'),dict) and claims['firebase'].get('sign_in_provider')=='password','Use Firebase Email/Password sign-in.',401)
        valid_since=user.get('validSince','0');require(re.fullmatch(r'[0-9]{1,12}',str(valid_since)),'Invalid Firebase account status.',401)
        require(not user.get('disabled',False) and claims['auth_time']>=int(valid_since),'Firebase account disabled or session revoked.',401,'FIREBASE_SESSION_REVOKED')
    except Problem:raise
    except Exception:raise Problem('Invalid Firebase token response.',401,'FIREBASE_AUTH_FAILED') from None
    # Return only the claims this application needs; never user passwordHash or Google refresh tokens.
    return {'uid':uid,'email':str(user.get('email',''))[:254],'name':str(user.get('displayName',''))[:120],
            'exp':claims['exp'],'auth_time':claims['auth_time'],'firebase':{'sign_in_provider':'password'},
            '_valid_after':int(valid_since)*1000}

def firebase_shared_account_enabled():
    value=cfg('FIREBASE_ALLOW_SHARED_ACCOUNT')
    return value is True or (isinstance(value,str) and value.strip().lower() in ('true','1'))

class FirebasePasswordSession:
    def __init__(self):
        self.uid=str(cfg('FIREBASE_BACKEND_UID'));self.email=str(cfg('FIREBASE_BACKEND_EMAIL'))
        self.password=str(cfg('FIREBASE_BACKEND_PASSWORD'))
        require(self.email and '@' in self.email and len(self.password)>=6 and re.fullmatch(r'[A-Za-z0-9_-]{1,128}',self.uid)
                and not self.uid.startswith(('REPLACE_','PASTE_')),
                'REST mode: privately fill FIREBASE_BACKEND_EMAIL, FIREBASE_BACKEND_PASSWORD and FIREBASE_BACKEND_UID in CONFIG.',503)
        require(firebase_shared_account_enabled() or self.uid not in FB_SUPER_UIDS|FB_ADMIN_UIDS,'Use a separate backend Firebase Auth account, or explicitly opt in with FIREBASE_ALLOW_SHARED_ACCOUNT=true.',503)
        require(cfg('FIREBASE_WEB_API_KEY') and re.fullmatch(r'[a-z0-9][a-z0-9-]{3,62}',str(cfg('FIREBASE_PROJECT_ID'))),
                'REST mode requires the public Web API key and matching Firebase project ID.',503)
        self.lock=threading.RLock();self._token='';self._refresh='';self._expires=0;self._checked=0
    def token(self):
        with self.lock:
            try:
                if self._expires<=now()+120:
                    response=None
                    if self._refresh:
                        try:response=firebase_identity('refresh',{'grant_type':'refresh_token','refresh_token':self._refresh})
                        except Problem as exc:
                            if exc.status!=401:raise
                    if response is None:
                        response=firebase_identity('signInWithPassword',{'email':self.email,'password':self.password,'returnSecureToken':True})
                    token=response.get('idToken',response.get('id_token',''))
                    uid=response.get('localId',response.get('user_id',''))
                    require(uid==self.uid,'Backend Auth UID does not match the configured account.',401)
                    claims=firebase_rest_verify(token,self.uid)
                    refresh=response.get('refreshToken',response.get('refresh_token',''))
                    require(isinstance(refresh,str) and 1<=len(refresh)<=8192,'Missing Firebase refresh token.',401)
                    self._token=token;self._refresh=refresh;self._expires=claims['exp'];self._checked=now()
                elif self._checked+60<=now():
                    firebase_rest_verify(self._token,self.uid);self._checked=now()
                return self._token
            except Problem as exc:
                if exc.status==401:
                    self._token='';self._refresh='';self._expires=0
                    raise Problem('Firebase backend account rejected. Check its private email/password, UID, project and enabled status.',503,'FIREBASE_BACKEND_AUTH') from None
                raise

class FirebaseREST:
    def __init__(self):
        url=str(cfg('FIREBASE_DATABASE_URL')).rstrip('/');parsed=urllib.parse.urlsplit(url)
        require(parsed.scheme=='https' and not parsed.username and not parsed.password and parsed.port in (None,443)
                and not parsed.path and not parsed.query and not parsed.fragment
                and re.fullmatch(r'[a-z0-9-]+(?:\.[a-z0-9-]+)?\.(?:firebaseio\.com|firebasedatabase\.app)',parsed.hostname or ''),
                'Use the exact HTTPS Firebase RTDB origin, without a path, credentials or query.',503)
        self.url=url;self.auth=FirebasePasswordSession()
    def call(self,method,path,*,value=None,etag=None,want_etag=False,shallow=False):
        parts=path.split('/')
        require(parts and all(re.fullmatch(r'[A-Za-z0-9_-]{1,128}',p) for p in parts),'Invalid database path.')
        headers={};params={'auth':self.auth.token()}
        if want_etag:headers['X-Firebase-ETag']='true'
        if shallow:params['shallow']='true'
        if etag is not None:
            require(isinstance(etag,str) and 1<=len(etag)<=256 and not any(ord(c)<32 for c in etag),'Missing/invalid Firebase ETag.',503,'FIREBASE_PROTOCOL')
            headers['if-match']=etag
        status,data,response_headers=firebase_http(method,self.url+'/'+path+'.json',params=params,payload=value,headers=headers)
        if status==412 and etag is not None:return status,data,response_headers
        if status in (401,403):raise Problem('Firebase denied database access. Check the backend UID and published UID-restricted rules.',503,'FIREBASE_PERMISSION_DENIED')
        require(status in (200,204),'Firebase database operation failed. Check storage availability and rules.',503,'FIREBASE_UNAVAILABLE')
        return status,data,response_headers

class FirebaseRESTReference:
    def __init__(self,client,path,shallow=False):self.client=client;self.path=path;self.is_shallow=shallow
    def child(self,path):return FirebaseRESTReference(self.client,self.path+'/'+path)
    def shallow(self):return FirebaseRESTReference(self.client,self.path,True)
    def get(self):return self.client.call('GET',self.path,shallow=self.is_shallow)[1]
    def set(self,value):self.client.call('PUT',self.path,value=value)
    def delete(self):self.client.call('DELETE',self.path)
    def transaction(self,callback):
        # Only a definitive HTTP 412 retries the pure callback. Never replay after ambiguous network/write failure.
        for attempt in range(4):
            _,current,headers=self.client.call('GET',self.path,want_etag=True)
            etag=next((v for k,v in headers.items() if k.lower()=='etag'),None)
            require(etag is not None,'Firebase omitted the transaction ETag.',503,'FIREBASE_PROTOCOL')
            proposed=callback(copy.deepcopy(current))
            if proposed==current:return proposed  # read-only/no-op transaction: no write to contend over
            status,_,_=self.client.call('PUT',self.path,value=proposed,etag=etag)
            if status!=412:return proposed
        raise Problem('Firebase transaction contention. Refresh before retrying.',503,'FIREBASE_CONFLICT')

def firebase_login_available():
    return bool(store and (getattr(store,'firebase_app',None) or getattr(store,'rest_client',None)))


class Store:
    """Small-install atomic state. Firebase transaction callbacks must have no network effects.
    Whole-state transactions intentionally prioritize simple cross-instance consistency over scale.
    """
    def __init__(self):
        self.kind="sqlite"; self.ref=None; self.root=None; self.firebase_app=None; self.rest_client=None; self.lock=threading.RLock()
        if not DEMO and cfg("FIREBASE_ACCESS_MODE")=="rest":
            require(cfg("FIREBASE_DATABASE_URL"),"REST mode requires FIREBASE_DATABASE_URL; refusing ephemeral SQLite fallback.",503)
        if cfg("FIREBASE_DATABASE_URL") and not DEMO:
            mode=str(cfg('FIREBASE_ACCESS_MODE'))
            require(mode in ('rest','sdk'),'FIREBASE_ACCESS_MODE must be rest or sdk.',503)
            ns=str(cfg('FIREBASE_NAMESPACE'));require(re.fullmatch(r'[A-Za-z0-9_-]{1,50}',ns),'Invalid Firebase namespace.',503)
            if mode=='rest':
                self.rest_client=FirebaseREST();self.root=FirebaseRESTReference(self.rest_client,ns)
                self.ref=self.root.child('state');self.kind='firebase'
            else:
                import firebase_admin
                from firebase_admin import credentials, db
                raw=cfg("FIREBASE_SERVICE_ACCOUNT")
                require(bool(raw),"Firebase service-account JSON/path is required.")
                cred=raw if isinstance(raw,dict) else (json.loads(raw) if str(raw).lstrip().startswith("{") else str(raw))
                certificate=credentials.Certificate(cred)
                if cfg('FIREBASE_PROJECT_ID'):
                    require(getattr(certificate,'project_id',None)==str(cfg('FIREBASE_PROJECT_ID')),'Firebase service account project does not match FIREBASE_PROJECT_ID.')
                fa=firebase_admin.initialize_app(certificate,{"databaseURL":cfg("FIREBASE_DATABASE_URL"),"httpTimeout":8},name="srdark")
                ns=str(cfg("FIREBASE_NAMESPACE"))
                require(bool(re.fullmatch(r"[A-Za-z0-9_-]{1,50}",ns)),"Invalid Firebase namespace.")
                self.firebase_app=fa; self.root=db.reference(ns,app=fa); self.ref=self.root.child("state"); self.kind="firebase"
        else:
            require(not os.environ.get("VERCEL") or DEMO,"Vercel requires Firebase; local SQLite is ephemeral.")
            self.path="data/demo.sqlite3" if DEMO else str(cfg("SQLITE_PATH"))
            Path(self.path).parent.mkdir(parents=True,exist_ok=True)
            with self.connect() as c:
                c.execute("CREATE TABLE IF NOT EXISTS state (id INTEGER PRIMARY KEY CHECK(id=1), payload TEXT NOT NULL)")
                c.execute("INSERT OR IGNORE INTO state VALUES(1,?)",(json.dumps(fresh()),))
    @contextmanager
    def connect(self):
        c=sqlite3.connect(self.path,timeout=12); c.execute("PRAGMA busy_timeout=12000")
        try:
            with c: yield c
        finally: c.close()
    def read(self):
        if self.ref:
            value=self.ref.get()
            return normalize(json.loads(value) if isinstance(value,str) else value)
        with self.connect() as c: return normalize(json.loads(c.execute("SELECT payload FROM state WHERE id=1").fetchone()[0]))
    def tx(self, fn):
        if self.ref:
            result=[None]
            def update(s):
                s=normalize(json.loads(s) if isinstance(s,str) else s); result[0]=fn(s)
                return json.dumps(s,ensure_ascii=False,allow_nan=False)
            self.ref.transaction(update); return result[0]
        with self.lock, self.connect() as c:
            c.execute("BEGIN IMMEDIATE")
            s=normalize(json.loads(c.execute("SELECT payload FROM state WHERE id=1").fetchone()[0]))
            result=fn(s)
            c.execute("UPDATE state SET payload=? WHERE id=1",(json.dumps(s,ensure_ascii=False,allow_nan=False),))
            return result
    def put_backup(self,key,blob,keep):
        if self.root:
            self.root.child("backups/"+key).set({"t":now(),"encrypted":blob.decode()})
            existing=self.root.child("backups").shallow().get() or {}
            for k in sorted(existing)[:-keep]: self.root.child("backups/"+k).delete()
        else:
            p=Path("data/demo-backups" if DEMO else str(cfg("BACKUP_DIR"))); p.mkdir(parents=True,exist_ok=True)
            f=p/(key+".enc"); f.write_bytes(blob); f.chmod(0o600)
            for old in sorted(p.glob("*.enc"))[:-keep]: old.unlink()
    def get_backup(self,key):
        require(bool(re.fullmatch(r"[0-9A-Za-z_-]+",key)),"Invalid backup ID.")
        if self.root:
            v=self.root.child("backups/"+key).get()
            require(bool(v),"Backup expired from retention.",404)
            return v["encrypted"].encode()
        p=Path("data/demo-backups" if DEMO else str(cfg("BACKUP_DIR"))) / (key+".enc")
        require(p.exists(),"Backup expired from retention.",404); return p.read_bytes()

store=None; SETUP_ERROR=""
secret=str(cfg("SECRET_KEY"))
if DEMO: secret="demo-only-not-for-production-"+"a"*40
try:
    if not DEMO:
        require(len(secret)>=32,"Set SECRET_KEY (32+ random characters).")
        require(bool(SUPER_IDS or FB_SUPER_UIDS),"Set FIREBASE_SUPER_ADMIN_UIDS or a Telegram SUPER_ADMIN_IDS owner.")
        if FB_SUPER_UIDS or FB_ADMIN_UIDS:
            require(bool(cfg("FIREBASE_WEB_API_KEY")) and bool(cfg("FIREBASE_DATABASE_URL")) and (cfg("FIREBASE_ACCESS_MODE")=="rest" or bool(cfg("FIREBASE_SERVICE_ACCOUNT"))),
                "Firebase admin login needs the Web API key, database URL and configured REST backend or legacy SDK credentials.")
            require(all(re.fullmatch(r"[A-Za-z0-9_-]{1,128}",u) for u in FB_SUPER_UIDS | FB_ADMIN_UIDS),"Copy the Firebase Authentication UID, not email, into the admin UID allowlist.")
        require(bool(re.fullmatch(r"[A-Za-z0-9_-]{32,256}",str(cfg("WEBHOOK_SECRET")))),"Set WEBHOOK_SECRET (32+ letters/digits/_/-).")
        require(len(str(cfg("CRON_SECRET")))>=32,"Set CRON_SECRET (32+ characters).")
        base_url=urllib.parse.urlsplit(str(cfg("BASE_URL")))
        require(base_url.scheme=="https" and base_url.hostname and not base_url.username and not base_url.password
            and base_url.path in ("","/") and not base_url.query and not base_url.fragment and len(str(cfg("BASE_URL")))<=256,
            "Set BASE_URL to a public HTTPS origin only (no path, credentials, query or fragment).")
        require(bool(cfg("BOT_TOKEN")),"Set BOT_TOKEN. BOT_USERNAME is optional and discovered during webhook setup.")
    store=Store()
except Exception as e:
    SETUP_ERROR=e.message if isinstance(e,Problem) else "Database initialization failed. Check private server configuration."
    LOG.warning("Setup incomplete: %s",SETUP_ERROR)
app=Flask(__name__)
app.secret_key=secret or secrets.token_hex(32)
app.json=StrictJSONProvider(app)
app.config.update(MAX_CONTENT_LENGTH=5*1024*1024,SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SECURE=not DEMO,SESSION_COOKIE_SAMESITE="Strict",
    SESSION_COOKIE_NAME="srd_demo" if DEMO else "__Host-srd_session",SESSION_COOKIE_PATH="/",PERMANENT_SESSION_LIFETIME=timedelta(hours=8))

if not DEMO and store:
    primary=urllib.parse.urlsplit(str(cfg("BASE_URL"))).hostname
    extra=[x.strip().lower() for x in str(cfg("EXTRA_HOSTS") or "").split(",") if x.strip()]
    if any(not re.fullmatch(r"[a-z0-9][a-z0-9.-]*",h) for h in extra):
        SETUP_ERROR="EXTRA_HOSTS must contain exact hostnames, not URLs or wildcard patterns."
        store=None
    else: app.config["TRUSTED_HOSTS"]=[primary]+extra

# Bounded admission throttling: happens BEFORE Firebase reads, JSON parsing and Telegram calls.
# Fixed 60-second windows; per-process fallback is not distributed DDoS protection.
class AdmissionLimiter:
    LUA = """local n=redis.call('INCR',KEYS[1]); if n==1 then redis.call('EXPIRE',KEYS[1],ARGV[1]) end; return n"""
    def __init__(self):
        self.buckets={}; self.lock=threading.RLock(); self.redis=None; self.redis_url=None
    def hit(self,scope,identity,limit,local_only=False):
        stamp=now(); bucket=stamp//60; key=f"{scope}:{digest(identity)[:32]}:{bucket}"
        if cfg("REDIS_URL") and not local_only:
            try:
                with self.lock:
                    if self.redis is None or self.redis_url!=cfg("REDIS_URL"):
                        import redis
                        self.redis=redis.Redis.from_url(str(cfg("REDIS_URL")),socket_connect_timeout=1,
                            socket_timeout=1,max_connections=12,decode_responses=True)
                        self.redis_url=cfg("REDIS_URL")
                count=int(self.redis.eval(self.LUA,1,str(cfg("REDIS_PREFIX"))+":"+key,120))
            except Exception:
                # No unbounded fallback when the configured shared limiter is unavailable.
                raise Problem("Traffic guard unavailable. Retry shortly.",503,"GUARD_UNAVAILABLE")
        else:
            with self.lock:
                if len(self.buckets)>=4096:
                    self.buckets={k:v for k,v in self.buckets.items() if v[1]>stamp}
                require(key in self.buckets or len(self.buckets)<8192,
                    "Traffic guard is at capacity. Retry shortly.",503,"GUARD_CAPACITY")
                count=self.buckets.get(key,(0,0))[0]+1
                self.buckets[key]=(count,(bucket+2)*60)
        require(count<=limit,"Too many requests. Retry after the current minute.",429,"HTTP_RATE_LIMIT")

limiter=AdmissionLimiter()
def client_address():
    peer=request.remote_addr or "unknown"
    # X-Forwarded-For is untrusted by default. The configured number refers to trusted hops
    # from the RIGHT, never the attacker-controlled leftmost entry.
    hops=max(0,min(3,int(cfg("TRUST_PROXY_HOPS") or 0)))
    if hops:
        chain=[x.strip() for x in request.headers.get("X-Forwarded-For","").split(",")]
        if len(chain)>=hops: peer=chain[-hops]
    try: return str(ipaddress.ip_address(peer))
    except ValueError: return request.remote_addr or "unknown"

@app.before_request
def admission_guard():
    g.csp_nonce=secrets.token_urlsafe(20)
    require(len(request.full_path)<=4096,"Request URL too long.",414,"URL_TOO_LONG")
    require(sum(len(k)+len(v) for k,v in request.headers.items())<=16384,
        "Request headers too large.",431,"HEADERS_TOO_LARGE")
    path=request.path; ip=client_address()
    if path in ("/login/firebase","/manage/security/firebase"): max_body=12*1024
    elif path=="/manage/restore": max_body=4500*1024
    elif path=="/telegram/webhook": max_body=64*1024
    elif path in ("/login","/demo-login","/tasks/tick","/ops/webhook"): max_body=2048
    elif path.startswith("/api/"): max_body=0
    else: max_body=512*1024
    request.max_content_length=max_body
    require(not request.content_length or request.content_length<=max_body,
        "Request body too large.",413,"BODY_TOO_LARGE")
    if path=="/health":
        limiter.hit("health",ip,120); return
    # Cheap invalid-secret rejection protects Telegram and operator paths before Redis/DB.
    if path=="/telegram/webhook":
        supplied=request.headers.get("X-Telegram-Bot-Api-Secret-Token","")
        if DEMO or not cfg("WEBHOOK_SECRET") or not hmac.compare_digest(supplied,str(cfg("WEBHOOK_SECRET"))):
            limiter.hit("bad-hook",ip,10,local_only=True)
            raise Problem("Invalid webhook secret.",403,"FORBIDDEN")
        limiter.hit("trusted-hooks","telegram",max(120,int(cfg("HTTP_GLOBAL_RPM") or 1200)))
        return
    if path in ("/tasks/tick","/ops/webhook"):
        supplied=request.headers.get("Authorization","")
        if DEMO or not cfg("CRON_SECRET") or not hmac.compare_digest(supplied,"Bearer "+str(cfg("CRON_SECRET"))):
            limiter.hit("bad-operator",ip,10,local_only=True)
            raise Problem("Invalid operator secret.",403,"FORBIDDEN")
        limiter.hit("operator",ip,10); return
    limiter.hit("global","requests",max(1,int(cfg("HTTP_GLOBAL_RPM") or 1200)))
    if path.startswith("/api/"): scope,cap="api",max(1,int(cfg("HTTP_API_RPM") or 180))
    elif path in ("/login","/login/firebase","/demo-login","/manage/security/firebase"): scope,cap="login",10
    elif request.method not in ("GET","HEAD","OPTIONS"): scope,cap="mutation",30
    else: scope,cap="read",120
    limiter.hit(scope,ip,cap)

_IDENTITY_CACHE={"username":"","until":0}
_IDENTITY_LOCK=threading.RLock()
def bot_username(state=None):
    if DEMO: return "SRDarkDemoBot"
    fallback=str(cfg("BOT_USERNAME") or "").lstrip("@")
    def extract(s):
        identity=s.get("system",{}).get("bot_identity",{})
        return identity.get("username","") if identity.get("token_fingerprint")==digest(cfg("BOT_TOKEN")) else ""
    if state is not None: return extract(state) or fallback
    # Root login view caches the verified identity; Telegram getMe is NEVER called anonymously.
    with _IDENTITY_LOCK:
        if _IDENTITY_CACHE["until"]>now(): return _IDENTITY_CACHE["username"] or fallback
        _IDENTITY_CACHE["until"]=now()+60
        if store:
            try: _IDENTITY_CACHE["username"]=extract(store.read())
            except Exception: pass
        return _IDENTITY_CACHE["username"] or fallback

def api_links(state,a,key):
    base=str(cfg("BASE_URL")).rstrip("/")
    if DEMO and not base:
        base=request.host_url.rstrip("/") if has_request_context() else "http://localhost:8080"
    endpoint=base+"/api/"+a["id"]
    src=state["catalog"].get(a.get("catalog_id"),{}) if a["mode"]=="catalog" else a
    query={} if a.get("header_only") else {"key":key}
    param=src.get("param","value") if src.get("mode") in ("proxy","validation") else ""
    sample=str(src.get("example_value", "")) if param else ""
    if param: query[param]=sample or "VALUE"  # legacy endpoints only; all new proxy sources require an example
    request_query={param:sample or 'VALUE'} if param else {}
    request_url=endpoint+('?' + urllib.parse.urlencode(request_query) if request_query else '')
    ready_url=endpoint+('?' + urllib.parse.urlencode(query) if query else '')
    # POSIX shell quoting; user-provided examples cannot escape the generated command.
    from shlex import quote
    lines=['SR DARK — PRIVATE API CREDENTIALS','Keep this file private. It contains your API key.',
           'Name: '+a['name'],'API ID: '+a['id'],'API key: '+key,'Request URL (no key): '+request_url,
           'Authentication: X-API-Key header'+(' REQUIRED; query keys disabled.' if a.get('header_only') else ' recommended.'),
           'Input parameter: '+(param or '(none)'),
           'Expires: '+iso(a['expires']),f"Limits: {a['daily']}/day; {a['rpm']}/minute",
           'curl '+quote(request_url)+' -H '+quote('X-API-Key: '+key)]
    if not a.get('header_only'):lines+=['','Legacy keyed URL (do not paste into chats; previews can call it):',ready_url]
    if a.get('plan_snapshot'):lines+=['Plan: '+a['plan_snapshot']['name']+' — '+plan_summary(a['plan_snapshot'])]
    if a.get('is_trial'):lines+=['Trial total budget: '+str(a['trial_limit'])+'; no reset or renewal.']
    return {'endpoint':endpoint,'ready_url':ready_url,'request_url':request_url,'parameter':param,
        'example_value':sample,'needs_value':bool(param and not sample),'header_only':bool(a.get('header_only')),
        'credential_text':'\n'.join(lines)+'\n'}


def settings_validate(data):
    validate_json_tree(data)
    require(not set(data)&{"SUPER_ADMIN_IDS","FIREBASE_SUPER_ADMIN_UIDS","super_admin_ids","owner_id"},"Owner identities are hosting-CONFIG-only.",403)
    out={}
    for k,lo,hi in [('bot_user_rpm',10,120),('bot_admin_rpm',25,300),('starter_days',1,30),('starter_daily',1,10000),('starter_rpm',1,1000),('starter_extend_price',1,1000000),('starter_extend_days',1,30),('starter_quota_price',1,1000000),('starter_quota_add',1,10000),('custom_key_price',1,1000000),('web_unlock_minutes',5,120)]:
        if k in data:out[k]=integer(data[k],k,lo,hi)
    if 'key_style' in data:
        require(data['key_style'] in ('legacy','droid15'),'Choose legacy or droid15 key style.');out['key_style']=data['key_style']
    for k in ('modern_controls','safe_chat_receipts','starter_enabled','owner_approval_required'):
        if k in data:require(type(data[k]) is bool,k+' must be boolean.');out[k]=data[k]
    for k,low,high in [("trial_minutes",1,1440),("trial_requests",1,10000),("trial_rpm",1,1000),("default_api_price",1,1000000),("referral_reward",1,1000000),("referral_new_user_reward",0,1000000),("diamond_coin_rate",0,1000000),("daily_limit",1,100000),("valid_days",1,365),
        ("rpm",1,1000),("max_apis",1,100),("max_payload_kb",1,256),("backup_hours",1,168),("backup_keep",2,30)]:
        if k in data:
            if k in ("trial_minutes","trial_requests","trial_rpm","default_api_price","referral_reward","referral_new_user_reward","diamond_coin_rate"):
                require(type(data[k]) is int,k+" must be a whole-number JSON integer.")
            try: n=int(data[k])
            except (ValueError,TypeError): raise Problem(k+" must be an integer.")
            require(low<=n<=high,f"{k}: allowed range {low}–{high}."); out[k]=n
    if 'backup_delivery' in data:
        require(data['backup_delivery'] in ('logs','owner','both'),'Choose logs, owner or both for encrypted backup delivery.')
        out['backup_delivery']=data['backup_delivery']
    if 'purchase_packs' in data:out['purchase_packs']=package_validate(data['purchase_packs'])
    for k,limit in [('developer_username',32),('support_username',32),('developer_name',60),('developer_about',1000),('developer_website',300),('payment_terms',1500)]:
        if k in data:
            require(isinstance(data[k],str) and len(data[k])<=limit and not any(ord(c)<32 and c not in '\n\t' for c in data[k]),'Invalid '+k)
            value=data[k].strip()
            if k in ('support_username','developer_username'):
                value=value.lstrip('@');require(not value or re.fullmatch(r'[A-Za-z0-9_]{5,32}',value),'Use a Telegram username without a link.')
            if k=='developer_website' and value:
                link=urllib.parse.urlsplit(value);require(link.scheme=='https' and link.hostname and not link.username and not link.password,'Developer website must be HTTPS without credentials.')
            if k=='payment_terms':require(bool(value),'Payment terms cannot be empty.')
            out[k]=value
    for k in ("referral_approval","allow_custom","trial_enabled","api_receipts_txt","admin_event_notifications","default_header_only"):
        if k in data: require(isinstance(data[k],bool),k+" must be boolean."); out[k]=data[k]
    if "allowed_hosts" in data:
        hosts=data["allowed_hosts"]
        require(isinstance(hosts,list) and len(hosts)<=40,"Use up to 40 exact hostnames.")
        require(all(isinstance(h,str) and re.fullmatch(r"[a-zA-Z0-9.-]{3,253}",h) for h in hosts),"Hostnames only; no URLs/wildcards.")
        out["allowed_hosts"]=[h.lower() for h in hosts]
    if "replace" in data:
        rules=data["replace"]
        require(isinstance(rules,list) and len(rules)<=30,"Use up to 30 replacement pairs.")
        require(all(isinstance(p,list) and len(p)==2 and all(isinstance(x,str) and len(x)<=150 for x in p) and p[0] for p in rules),"Replacement format: [[find, replace]].")
        out["replace"]=rules
    if "inject" in data:
        require(isinstance(data["inject"],dict) and len(json.dumps(data["inject"]))<=4096,"Inject must be a JSON object up to 4KB.")
        out["inject"]=data["inject"]
    for k in ("error_expired","error_daily","error_key"):
        if k in data: require(isinstance(data[k],str) and 1<=len(data[k])<=300,"Error text must be 1–300 characters."); out[k]=data[k]
    return out

def source_validate(d, settings):
    name=str(d.get("name","")).strip(); require(1<=len(name)<=60,"Name must be 1–60 characters.")
    mode=d.get("mode","static"); require(mode in ("static","proxy","validation"),"Choose static, proxy or safe validation.")
    result={"name":name,"mode":mode,"param":str(d.get("param","value")),"url":"","data":None,
        "example_value":str(d.get("example_value", "")).strip()}
    require(len(result["example_value"])<=200 and not any(ord(c)<32 for c in result["example_value"]),
        "Example value: up to 200 characters, no control characters.")
    require(bool(re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{0,30}",result["param"])),"Invalid query parameter.")
    require(result["param"]!="key","The parameter name key is reserved for authentication; use value instead.")
    if 'demo_response' in d:
        validate_json_tree(d['demo_response'])
        require(len(json.dumps(d['demo_response'],ensure_ascii=False).encode())<=1200,'Demo response must be a small synthetic JSON sample (up to 1200 bytes).')
        result['demo_response']=copy.deepcopy(d['demo_response'])
    if mode=='validation':
        kind=d.get('validator','phone_format');require(kind in ('phone_format','aadhaar_checksum'),'Choose an available safe validator.')
        result['validator']=kind
        if not result['example_value']:result['example_value']='0000000000' if kind=='phone_format' else '000000000000'
        result['demo_response']=validation_result(kind,result['example_value'])
    elif mode=="static":
        data=d.get("data",{})
        validate_json_tree(data)
        require(len(json.dumps(data,ensure_ascii=False,allow_nan=False).encode())<=settings["max_payload_kb"]*1024,"JSON exceeds universal payload limit.")
        result["data"]=data
    else:
        u=re.sub(r"&(?:amp;)+", "&", str(d.get("url","")).strip()); p=urllib.parse.urlsplit(u)
        require(len(u)<=2000 and p.scheme=="https" and p.hostname and not p.username and not p.password and p.port in (None,443) and not p.fragment,"Only HTTPS URLs on port 443 without credentials/fragments.")
        require(p.hostname.lower() in settings["allowed_hosts"],"Source host must be approved in Settings → allowed_hosts. Only an owner may approve an exact trusted hostname; a source URL does not approve itself.",400,"SOURCE_HOST_NOT_APPROVED")
        result["url"]=u
    return result

def register(s,uid,name,ref=""):
    uid=str(uid)
    if uid in s["users"]: return s["users"][uid]
    require(len(s["users"])<3000,"Small-install user cap reached; migrate storage before growing.",503)
    u={"id":uid,"name":str(name)[:60],"role":"user","coins":0,"diamonds":0,"wallet_hold":False,"joined":now(),"blocked":False,
       "updates_on":False,"broadcast_hold":False,"broadcast_policy":"auto-start-v1","telegram_started":False,"last_active":now(),"campaign_events":{},"promo_pending":"",
       "active":uid in SUPER_IDS,"ref":ref if ref!=uid and ref in s["users"] else "", "refs":0,"flow":{}}
    s["users"][uid]=u;day_counter(s['system'],'new_users');audit(s,uid,"user.join","New account")
    if u['ref']:
        inviter=s['users'][u['ref']]
        soft_message(s,u['ref'],'*👋 New referral*\n'+md(u['name']+' opened your referral link. Rewards are pending all required joins and activation.'))
        soft_message(s,uid,'*💙 You were invited*\n'+md('Invited by '+inviter['name']+'. Complete all required joins and activate to qualify.'))
    notify_admins(s,"*New account*\n"+md(u["name"])+" · "+code(uid))
    return u

def activate(s,uid):
    u=actor(s,uid);require(joined(s,uid),'Join every required channel/group and use Verify all joins in the bot.',403,'JOIN_REQUIRED')
    if u.get('active'):return 'Account already active. Required joins verified.'
    u['active']=True;ref=u.get('ref')
    if ref and ref!=str(uid) and ref in s['users'] and not s['users'][ref].get('blocked') and str(uid) not in s['referrals']:
        s['referrals'][str(uid)]={'from':ref,'to':str(uid),'t':now(),'status':'pending',
            'reward':s['settings']['referral_reward'],'new_user_reward':s['settings']['referral_new_user_reward'],
            'join_revision':join_revision(s),'qualified_at':now()}
        if not s['settings']['referral_approval']:settle_referral(s,str(uid))
        else:
            notify_admins(s,'*Referral pending approval*\nNew user: '+code(uid))
            soft_message(s,ref,md('Referral joins and activation complete. Both rewards await admin approval.'))
    audit(s,uid,'user.activate');return 'Account activated. Share your referral link to earn coins.'

def owned(s,uid,aid):
    actor(s,uid); a=s["apis"].get(aid)
    require(a is not None,"API not found.",404)
    require(a["owner"]==str(uid) or is_admin(uid,s),"This API belongs to another user.",403)
    return a

def check_data_capacity(state):
    # This whole-state implementation is intentionally small-install, not unbounded storage.
    require(len(state["apis"])<=200,"Workspace API capacity reached (200). Migrate/partition storage before scaling.",409,"WORKSPACE_CAPACITY")
    compact={"apis":{k:{f:a.get(f) for f in ("name","mode","url","param","data","catalog_id","example_value","billing_currency","price","validator","demo_response")}
        for k,a in state["apis"].items()},"catalog":state["catalog"],"kv":state["kv"],
        "drafts":{k:u["flow"] for k,u in state["users"].items() if u.get("flow")}}
    compact.update(redeem_codes=state.get('redeem_codes',{}),credit_grants=state.get('credit_grants',{}),plans={k:a.get('plan_snapshot') for k,a in state['apis'].items() if a.get('plan_snapshot')})
    compact["trial_claims"]=state.get("trial_claims",{});compact["campaigns"]=state.get("campaigns",{});compact["engagement"]={k:state["settings"].get(k) for k in ("welcome_caption","welcome_links","welcome_photo","welcome_sticker","welcome_sticker_info","bot_text_style","force_join_channels","welcome_entities","button_icons")}
    require(len(json.dumps(compact,ensure_ascii=False,allow_nan=False).encode())<=2*1024*1024,
        "Workspace data/draft budget reached (2 MiB). Remove unused data or migrate storage.",409,"WORKSPACE_CAPACITY")

# Time-limited trials are separate keys/endpoints, never extensions of a paid API.
def trial_policy(st):
    return {'minutes':st['trial_minutes'],'requests':st['trial_requests'],'rpm':st['trial_rpm']}

def create_trial(s,uid,data):
    uid=str(uid);u=actor(s,uid);st=s['settings']
    require(uid.isdigit() and (u.get('telegram_started') or DEMO),'Open /start from your Telegram account before claiming a trial.',403,'TRIAL_ACCOUNT')
    require(st['trial_enabled'],'Free trials are currently disabled.',403,'TRIAL_DISABLED')
    require(u.get('active') and joined(s,uid),'Activate and verify all required joins in the bot first.',403,'JOIN_REQUIRED')
    require(not u.get('wallet_hold'),'Resolve your wallet hold before requesting a trial.',403,'WALLET_HOLD')
    require(uid not in s['trial_claims'],'Your one-time trial has already been claimed. See My APIs or choose a paid plan.',409,'TRIAL_USED')
    require(len(s['trial_claims'])<3000,'Trial history capacity reached. Contact the owner.',503,'TRIAL_CAPACITY')
    require(sum(a['owner']==uid for a in s['apis'].values())<st['max_apis'],'Maximum API slots reached.')
    require(isinstance(data,dict) and set(data)<={'catalog_id','quote'},'Use a catalogue source and the current trial quote.')
    require(data.get('quote')==trial_policy(st),'Trial policy changed or quote missing. Refresh and confirm the current policy.',409,'TRIAL_QUOTE_CHANGED')
    cid=str(data.get('catalog_id',''));src=s['catalog'].get(cid)
    require(src and src.get('enabled') and src.get('trial_enabled',False),'This source is not enabled for trials.',403,'TRIAL_SOURCE')
    if src['mode']=='proxy':require(bool(src.get('example_value')),'Admin must save a safe example before enabling this trial.')
    aid=new_id('api_');key=credential_key(s);started=now();deadline=started+st['trial_minutes']*60
    a={'id':aid,'name':clip_text(src['name'],50)+' · Trial','mode':'catalog','catalog_id':cid,'owner':uid,'key_hash':digest(key),
       'active':True,'public':False,'billing_currency':'coins','price':0,'is_trial':True,'header_only':bool(st.get('default_header_only')),
       'trial_limit':st['trial_requests'],'trial_deadline':deadline,'trial_minutes':st['trial_minutes'],
       'daily':st['trial_requests'],'rpm':st['trial_rpm'],'expires':deadline,'created':started,
       'calls':0,'errors':0,'day':utc_day(),'used':0,'minute':0,'minute_used':0,'history':[]}
    s['apis'][aid]=a
    s['trial_claims'][uid]={'api_id':aid,'catalog_id':cid,'claimed_at':started,'expires':deadline,'requests':a['trial_limit']}
    check_data_capacity(s);audit(s,uid,'api.trial.create',aid)
    return {'id':aid,'key':key,'name':a['name'],'expires':deadline,'daily':a['daily'],'is_trial':True,
            'trial_limit':a['trial_limit'],'trial_remaining':a['trial_limit'],**api_links(s,a,key)}

def trial_state(s,uid):
    st=s['settings'];claim=s['trial_claims'].get(str(uid))
    return {'enabled':st['trial_enabled'],**trial_policy(st),'claim':copy.deepcopy(claim),
            'sources':[{'id':c['id'],'name':c['name'],'mode':c['mode']} for c in s['catalog'].values() if c.get('enabled') and c.get('trial_enabled')]}

def trial_menu(s,uid):
    t=trial_state(s,uid)
    if t['claim']:
        claim=t['claim'];a=s['apis'].get(claim['api_id'])
        state='expired' if claim['expires']<=now() else 'claimed'
        text='*⏱ Your API trial*\n'+md(f"Already {state}. Deadline: {iso(claim['expires'])}\nOne claim per Telegram account; deleting or rotating keys does not reset it. Paid APIs remain separate.")
        return text,[[btn('Manage trial','api:'+a['id'])]]+[[btn('Paid API catalogue','create')]] if a and a['owner']==str(uid) else [[btn('Paid API catalogue','create')]]
    text='*⏱ '+md('One-time API trial')+'*\n\n'+md(f"{t['minutes']} minutes · {t['requests']} requests TOTAL · {t['rpm']}/minute\nFree: no coins or diamonds deducted. The clock starts when you confirm, not on the first API call. Pausing does not stop the clock. Expiry and total budget do not reset at midnight.")
    if not t['enabled']:return text+'\n\n'+md('Trials are disabled by the owner.'),[[btn('Home','home')]]
    if not t['sources']:return text+'\n\n'+md('No trial source is enabled yet. The owner must opt in a source in API catalogue.'),[[btn('Home','home')]]
    return text,[[btn(c['name'],'trialpick:'+c['id'],'success')] for c in t['sources'][:20]]+[[btn('Home','home')]]



def validate_source_plans(value):
    require(isinstance(value,list) and len(value)<=8,'Use up to eight plans per source.')
    result=[];seen=set()
    for item in value:
        require(isinstance(item,dict),'Invalid plan.')
        pid=item.get('id','');require(isinstance(pid,str) and re.fullmatch(r'[A-Za-z0-9_-]{1,16}',pid) and pid not in seen,'Plan IDs must be unique, 1–16 letters/digits/dash/underscore.');seen.add(pid)
        name=str(item.get('name','')).strip();require(1<=len(name)<=40,'Plan name: 1–40 characters.')
        require(type(item.get('enabled',True)) is bool,'Plan enabled must be boolean.')
        result.append({'id':pid,'name':name,'price':integer(item.get('price'),'Plan coins',1,1000000),
            'days':integer(item.get('days'),'Plan days',1,365),'daily':integer(item.get('daily'),'Daily requests',1,100000),
            'rpm':integer(item.get('rpm',30),'Plan RPM',1,1000),'total':integer(item.get('total',0),'Total budget',0,100000000),
            'enabled':item.get('enabled',True),'billing_currency':'coins'})
    return result

def selected_plan(src,pid):
    plan=next((p for p in src.get('plans',[]) if p['id']==pid and p.get('enabled',True)),None)
    require(plan is not None,'Choose an available plan again.',409,'PLAN_UNAVAILABLE')
    return copy.deepcopy(plan)

def plan_summary(plan):
    return f"{plan['price']} coins · {plan['days']} days · {plan['daily']}/day · {plan['rpm']}/min"+(f" · {plan['total']} total" if plan.get('total') else '')

def create_api(s,uid,d):
    u=actor(s,uid); st=s["settings"]; require(u.get("active"),"Activate your account first.",403)
    require(joined(s,uid),"Verify all required channel/group joins in the bot first.",403,"JOIN_REQUIRED")
    require(sum(a["owner"]==str(uid) for a in s["apis"].values())<st["max_apis"],"Maximum API slots reached.")
    cid=str(d.get("catalog_id", ""))
    if simple_ui(s) and not is_admin(uid,s):require(bool(cid),'Choose an API from the store; custom creation is disabled.',403,'CUSTOM_DISABLED')
    if cid:
        src=s["catalog"].get(cid); require(src and src.get("enabled"),"Catalogue entry unavailable.")
        if src["mode"] in ("proxy","validation"): require(bool(src.get("example_value")),"Admin must save an example value for this catalogue source first.")
        name=str(d.get("name") or src["name"])[:60]; source={"name":name,"mode":"catalog","catalog_id":cid}
    else:
        require(st["allow_custom"] or is_admin(uid,s),"Custom APIs disabled.",403)
        source=source_validate(d,st)
        if source["mode"] in ("proxy","validation"): require(bool(source["example_value"]),"Set an example value for the complete URL.")
    plan=None
    if cid and src.get('plans'):
        plan=selected_plan(src,str(d.get('plan_id','')))
        require(d.get('quote_plan')==plan,'Plan changed. Select it again and confirm the new limits/price.',409,'PLAN_CHANGED')
    elif d.get('plan_id') or d.get('quote_plan'):
        raise Problem('Plan removed. Choose a source and plan again.',409,'PLAN_CHANGED')
    currency,price=api_price(s,plan or (src if cid else None))
    if 'quote_price' in d or 'quote_currency' in d:
        require(d.get('quote_price')==price and d.get('quote_currency')==currency,'API price changed. Refresh and confirm the new price.',409)
    source.update(billing_currency=currency,price=price)
    charge_api(s,uid,currency,price,"new API")
    aid=new_id("api_"); key=credential_key(s)
    a={**source,"id":aid,"owner":str(uid),"key_hash":digest(key),"active":True,"public":False,"header_only":bool(st.get("default_header_only")),
       "daily":st["daily_limit"],"rpm":st["rpm"],"expires":now()+st["valid_days"]*86400,
       "created":now(),"calls":0,"errors":0,"day":utc_day(),"used":0,"minute":0,"minute_used":0,"history":[]}
    if plan:
        a.update(plan_snapshot=plan,plan_id=plan['id'],daily=plan['daily'],rpm=plan['rpm'],
                 total_limit=plan['total'],expires=now()+plan['days']*86400)
    s["apis"][aid]=a; check_data_capacity(s); audit(s,uid,"api.create",aid)
    return {"id":aid,"key":key,"name":a["name"],"expires":a["expires"],"daily":a["daily"],"rpm":a["rpm"],"plan":copy.deepcopy(a.get("plan_snapshot")),"total_limit":a.get("total_limit",0),**api_links(s,a,key)}

def api_action(s,uid,aid,action,d=None):
    d=d or {}; a=owned(s,uid,aid); st=s["settings"]; result={"message":"Saved."}
    if a.get('is_trial'):
        require(action!='renew','A trial cannot be renewed. Create a separate paid API from the catalogue.',409,'TRIAL_IMMUTABLE')
        require(action!='edit' or set(d)<={'name'},'Trial deadlines, source, limits and private-key requirement cannot be edited.',409,'TRIAL_IMMUTABLE')
        require(action!='toggle' or not a.get('trial_invalidated'),'Restored trial keys are invalidated. Create a paid API instead.',409,'TRIAL_RESTORED')
    if a.get("is_starter") and action=="renew":raise Problem("Use starter upgrades: the price is shown before confirmation.",409)
    if action=="delete": del s["apis"][aid]; result={"message":"API deleted. No referral refund."}
    elif action=="toggle": a["active"]=not a["active"]
    elif action=="rotate":
        key=credential_key(s,a.get("key_label","")); a["key_hash"]=digest(key); result={"key":key,"id":aid,**api_links(s,a,key)}
    elif action=="renew":
        u=actor(s,uid)
        currency,price=api_price(s,a);charge_api(s,uid,currency,price,aid)
        plan=a.get('plan_snapshot')
        a['expires']=max(now(),a['expires'])+(plan['days'] if plan else st['valid_days'])*86400
        a['daily']=plan['daily'] if plan else st['daily_limit'];a['rpm']=plan['rpm'] if plan else st['rpm']
        if plan and plan.get('total'):a['total_limit']=a.get('total_limit',plan['total'])+plan['total']
        result={"message":"Renewed; today's usage is retained.","expires":a["expires"]}
    elif action=="edit":
        if simple_ui(s) and not is_admin(uid,s) and a["mode"]!="catalog":require(set(d)<={"name"},"Custom source editing is disabled.",403,"CUSTOM_DISABLED")
        if a["mode"]=="catalog":
            name=str(d.get("name",a["name"])).strip(); require(1<=len(name)<=60,"Invalid name."); a["name"]=name
        else:
            src=source_validate({**a,**{k:d[k] for k in ("name","mode","url","param","data","example_value") if k in d}},st)
            if src["mode"] in ("proxy","validation"): require(bool(src["example_value"]),"Set an example value before saving this proxy API.")
            a.update(src)
        if is_admin(uid,s):
            for field,lo,hi in (("daily",1,100000),("rpm",1,1000)):
                if field in d:
                    value=integer(d[field],field,lo,hi); a[field]=value
            if 'total_limit' in d:a['total_limit']=integer(d['total_limit'],'Total cap',0,100000000)
            if 'expires_at' in d:
                require(not d.get('extend_days'),'Use exact expiry OR extend days, not both.')
                a['expires']=integer(d['expires_at'],'Expiry timestamp',now()-86400,now()+5*365*86400)
            if "extend_days" in d:
                days=integer(d["extend_days"],"Extend days",0,365)
                if days: a["expires"]=max(a["expires"],now())+days*86400
            if 'header_only' in d:
                require(type(d['header_only']) is bool,'Header-only must be boolean.')
                require(not (d['header_only'] and d.get('public')),'Header-only endpoints cannot be public.')
                a['header_only']=d['header_only']
                if a['header_only']:a['public']=False
            if d.get('public'):require(not a.get('header_only'),'Turn off header-only before enabling public access.')
            if "public" in d: require(isinstance(d["public"],bool),"public must be boolean."); a["public"]=d["public"]
    else: raise Problem("Unknown action.")
    if action=="edit": check_data_capacity(s)
    audit(s,uid,"api."+action,aid); return result

def admin_action(s,uid,kind,d):
    actor(s,uid,admin=True)
    if kind=='credit':return grant_credit(s,uid,d)
    if kind=='redeem':
        actor(s,uid,superonly=True)
        if d.get('revoke'):
            record=next((r for r in s['redeem_codes'].values() if r['id']==d.get('id')),None)
            require(record,'Code record not found.',404);record['enabled']=False;audit(s,uid,'redeem.revoke',record['id'])
            return {'message':'Code revoked. Existing credits are not reversed.'}
        return create_redeem(s,uid,d)
    if kind=="settings":
        actor(s,uid,superonly=True); change=settings_validate(d); s["settings"].update(change)
        if d.get("apply_existing"):
            for a in s["apis"].values():
                if a.get("is_trial") or a.get('is_starter') or a.get('plan_snapshot'):continue
                a["daily"]=s["settings"]["daily_limit"]; a["rpm"]=s["settings"]["rpm"]
        audit(s,uid,"settings.update",", ".join(change)); return {"message":"Settings saved. Existing expiry/usage preserved."}
    if kind=="user":
        target=str(d.get("id","")); u=s["users"].get(target); require(u is not None,"User not found.",404)
        require(target not in SUPER_IDS and not target.startswith("fb:"),"Telegram super-admins and Firebase admin roles are managed in server config.",403)
        was_admin=is_admin(target,s)
        if role(target,s)=="admin": actor(s,uid,superonly=True)
        if "role" in d:
            actor(s,uid,superonly=True); require(d["role"] in ("admin","user"),"Invalid role."); u["role"]=d["role"]
        if "blocked" in d:
            require(isinstance(d["blocked"],bool),"blocked must be boolean."); u["blocked"]=d["blocked"]
        for currency in ('coins','diamonds'):
            if currency in d:
                actor(s,uid,superonly=True);balance=integer(d[currency],currency,0,1000000000)
                wallet_change(s,target,currency,balance-u.get(currency,0),'Owner balance adjustment',str(uid))
                s['system']['external_payments']=True
        if d.get("delete"):
            actor(s,uid,superonly=True)
            require(not any(a["owner"]==target for a in s["apis"].values()),"Delete this user's APIs first.")
            # Keep a tombstone to prevent rejoining/referral farming.
            u.update(name="Deleted account",blocked=True,flow={},role="user")
        if was_admin or is_admin(target,s):queue_commands(s,target,force=True)
        audit(s,uid,"user.update",target); return {"message":"User updated."}
    if kind=="referral":
        rid=str(d.get("id","")); r=s["referrals"].get(rid)
        require(r and r["status"]=="pending","Referral is not pending.")
        approve=d.get('approve') is True
        if approve:settle_referral(s,rid)
        else:r['status']='rejected';audit(s,uid,'referral.rejected',rid)
        return {'message':'Referral reviewed. Both configured rewards are applied once on approval.'}
    if kind=="catalog":
        cid=str(d.get("id") or new_id("cat_"))
        if d.get("delete"):
            require(not any(a.get("catalog_id")==cid for a in s["apis"].values()),"Catalogue entry in use. Disable it instead.")
            s["catalog"].pop(cid,None)
        else:
            src=source_validate(d,s["settings"])
            if src["mode"] in ("proxy","validation"): require(bool(src["example_value"]),"Admin must set a public example value before publishing a proxy source.")
            currency=d.get('billing_currency','coins');require(currency in ('coins','diamonds'),'Choose coins or diamonds.')
            price=integer(d.get('price',s['settings']['default_api_price']),'API price')
            trial=d.get('trial_enabled',s['catalog'].get(cid,{}).get('trial_enabled',False))
            require(type(trial) is bool,'Trial opt-in must be boolean.')
            require(type(d.get('starter_enabled',False)) is bool,'Starter opt-in must be boolean.')
            src['plans']=validate_source_plans(d.get('plans',s['catalog'].get(cid,{}).get('plans',[])))
            s["catalog"][cid]={**src,"id":cid,"trial_enabled":trial,"starter_enabled":d.get("starter_enabled",s["catalog"].get(cid,{}).get("starter_enabled",False)),"enabled":d.get("enabled",True) is True,"billing_currency":currency,"price":price}
        if not d.get("delete"): check_data_capacity(s)
        audit(s,uid,"catalog.update",cid); return {"id":cid,"message":"Catalogue saved."}
    if kind=="kv":
        key=str(d.get("key","")); require(bool(re.fullmatch(r"[A-Za-z0-9_-]{1,64}",key)),"Key: letters, digits, underscore or dash.")
        if d.get("delete"): s["kv"].pop(key,None)
        else:
            require(len(json.dumps(d.get("value")).encode())<=s["settings"]["max_payload_kb"]*1024,"Value too large.")
            s["kv"][key]=d.get("value")
        if not d.get("delete"): check_data_capacity(s)
        audit(s,uid,"kv.update",key); return {"message":"Storage updated."}
    raise Problem("Unknown admin action.")

def redact_api(a,admin=False):
    a=copy.deepcopy(a); a.pop("key_hash",None)
    if not admin and a["mode"]=="catalog": a.pop("url",None); a.pop("data",None)
    a["used"]=a.get("used",0) if a.get("day")==utc_day() else 0
    a["status"]="paused" if not a["active"] else ("expired" if a["expires"]<=now() else "active")
    if a.get("is_trial") and a["status"]=="active" and a["calls"]>=a["trial_limit"]:a["status"]="exhausted"
    a["endpoint"]="/api/"+a["id"]
    if a.get('total_limit') and a['status']=='active' and a['calls']>=a['total_limit']:a['status']='exhausted'
    return a

def public_state(s,uid):
    u=actor(s,uid); admin=is_admin(uid,s); superadmin=role(uid,s)=="superadmin"
    me={k:v for k,v in u.items() if k!="flow"}; me["role"]=role(uid,s)
    st=copy.deepcopy(s["settings"])
    if not superadmin: st={k:st[k] for k in ("default_api_price","daily_limit","valid_days","rpm","allow_custom","max_apis","max_payload_kb","allowed_hosts","referral_approval","referral_reward","referral_new_user_reward","diamond_coin_rate","purchase_packs","support_username","developer_name","developer_username","developer_about","developer_website","payment_terms","trial_enabled","trial_minutes","trial_requests","trial_rpm","api_receipts_txt","admin_event_notifications","default_header_only")}
    result={"me":me,"apis":[redact_api(a,admin) for a in s["apis"].values() if admin or a["owner"]==str(uid)],
        "catalog":[copy.deepcopy(a) if admin else {"id":a["id"],"name":a["name"],"mode":a["mode"],"param":a.get("param",""),"example_value":a.get("example_value",""),"billing_currency":api_price(s,a)[0],"price":api_price(s,a)[1],"trial_enabled":bool(a.get("trial_enabled"))} for a in s["catalog"].values() if admin or a["enabled"]],
        "settings":st,"referral_url":"https://t.me/"+bot_username(s)+("" if str(uid).startswith("fb:") else "?start=ref_"+str(uid)),
        "referrals":[{**r,"id":k} for k,r in s["referrals"].items() if admin or r["from"]==str(uid)],
        "demo":DEMO,"storage":store.kind,"version":VERSION,"bot_username":bot_username(s),"security":security_summary(s,uid)}
    result['orders']=[{k:v for k,v in o.items() if k not in ('charge','checkout_id','payload')} for o in sorted(s['orders'].values(),key=lambda x:x['created'],reverse=True) if superadmin or o['uid']==str(uid)][:100]
    result['ledger']=[v for v in reversed(list(s['ledger'].values())) if superadmin or v['uid']==str(uid)][:100]
    result['engagement']=engagement_state(s,uid)
    result['trial']=trial_state(s,uid)
    result['statistics']=statistics(s,uid,admin)
    result['membership']={'required':bool(s['settings']['force_join_channels']),'verified':joined(s,uid),
                          'channels':copy.deepcopy(s['settings']['force_join_channels'])}
    if superadmin:
        result['redeem_codes']=[{**{k:v for k,v in r.items() if k!='claims'},'claimed':len(r['claims'])} for r in s['redeem_codes'].values()]
        result['operations']={k:copy.deepcopy(s['settings'][k]) for k in OPS_KEYS}
        result['firebase_connection']={'project_id':str(cfg('FIREBASE_PROJECT_ID') or ''),'storage':store.kind,
            'access_mode':str(cfg('FIREBASE_ACCESS_MODE')),'shared_account_enabled':firebase_shared_account_enabled(),'backend_credentials_configured':bool(cfg('FIREBASE_BACKEND_EMAIL') and cfg('FIREBASE_BACKEND_PASSWORD') and cfg('FIREBASE_BACKEND_UID')),'service_account_configured':bool(cfg('FIREBASE_SERVICE_ACCOUNT')),'web_key_configured':bool(cfg('FIREBASE_WEB_API_KEY')),
            'approved_admins_configured':bool(FB_SUPER_UIDS or FB_ADMIN_UIDS),
            'admin_login_configured':bool(firebase_login_available() and cfg('FIREBASE_WEB_API_KEY') and (FB_SUPER_UIDS or FB_ADMIN_UIDS)),
            'namespace':str(cfg('FIREBASE_NAMESPACE'))} 
    if admin:
        result['settings'].update({k:s['settings'][k] for k in ('modern_controls','key_style','safe_chat_receipts','owner_approval_required','web_unlock_minutes','starter_enabled','starter_days','starter_daily','starter_rpm','starter_extend_price','starter_extend_days','starter_quota_price','starter_quota_add','custom_key_price')})
        result['starter_claims_count']=len(s['starter_claims'])
    for source in result['catalog']:source['referral_hint']=referral_requirement(s,uid,source)
    if admin:
        result['notifications']=sorted(s.get('admin_notifications',{}).values(),key=lambda n:(n['t'],n['id']),reverse=True)[:100]
        result['notification_seen']=u.get('notification_seen',0);result['notification_seen_ids']=u.get('notification_seen_ids',[])
        result.update(users=[{k:v for k,v in u.items() if k!="flow"} | {"role":role(i,s)} for i,u in s["users"].items()],
          logs=sorted(s["logs"].values(),key=lambda x:x["t"],reverse=True)[:150], kv=s["kv"],
          system={k:v for k,v in s["system"].items() if k not in ("backup_lease","bot_identity")},pending=len(s["outbox"]))
    return result

# Upstream requests: exact admin allowlist + all DNS answers public + TLS to pinned IP.
# No user-provided headers, redirects or third-party CORS relays.
_PROXY_POOLS=threading.local()
@contextmanager
def pinned_proxy_pool(host,ip):
    options={'port':443,'server_hostname':host,'assert_hostname':host,'cert_reqs':'CERT_REQUIRED','timeout':urllib3.Timeout(connect=3,read=7),'retries':False}
    flag=cfg('PROXY_KEEPALIVE')
    if not (flag is True or str(flag).lower() in ('1','true','yes')):
        with urllib3.HTTPSConnectionPool(ip,**options) as pool:yield pool
        return
    pid=os.getpid()
    if getattr(_PROXY_POOLS,'pid',None)!=pid:
        for pool,_ in getattr(_PROXY_POOLS,'items',{}).values():pool.close()
        _PROXY_POOLS.items={};_PROXY_POOLS.pid=pid
    pools=_PROXY_POOLS.items;key=(host,ip);current=time.monotonic()
    for old,(pool,used) in list(pools.items()):
        if current-used>60:pool.close();del pools[old]
    if key not in pools:
        while len(pools)>=4:
            old=min(pools,key=lambda k:pools[k][1]);pools.pop(old)[0].close()
        pools[key]=(urllib3.HTTPSConnectionPool(ip,maxsize=1,block=True,**options),current)
    pool,_=pools[key];pools[key]=(pool,current)
    yield pool

def fetch_source(url,param,value,allowed,limit):
    p=urllib.parse.urlsplit(url); host=p.hostname
    require(host in allowed and p.scheme=="https" and p.port in (None,443),"Source host no longer approved.",502,"UPSTREAM_BLOCKED")
    query=urllib.parse.parse_qsl(p.query,keep_blank_values=True)
    query=[(k,v) for k,v in query if k!=param]+[(param,value)]
    path=urllib.parse.urlunsplit(("","",p.path or "/",urllib.parse.urlencode(query),""))
    try:
        ips=sorted({x[4][0] for x in socket.getaddrinfo(host,443,type=socket.SOCK_STREAM)})
        require(ips and all(ipaddress.ip_address(ip).is_global for ip in ips),"Source resolves to a private/reserved address.",502,"UPSTREAM_BLOCKED")
        with pinned_proxy_pool(host,ips[0]) as pool:
            r=pool.request("GET",path,headers={"Host":host,"Accept":"application/json","User-Agent":"SRDark/4"},redirect=False,preload_content=False)
            complete=False
            try:
                require(200<=r.status<300,"Upstream returned an error or redirect.",502,"UPSTREAM_ERROR")
                start=time.monotonic(); chunks=[]; count=0
                while True:
                    b=r.read(min(16384,limit+1-count),decode_content=True)
                    if not b:complete=True;break
                    count+=len(b); require(count<=limit,"Upstream response exceeds payload limit.",502,"UPSTREAM_SIZE")
                    require(time.monotonic()-start<9,"Upstream timed out.",504,"UPSTREAM_TIMEOUT"); chunks.append(b)
                try: return strict_json(b"".join(chunks))
                except Problem: raise Problem("Upstream returned invalid, ambiguous or overly complex JSON.",502,"UPSTREAM_JSON")
            finally:
                if not complete and hasattr(r,"close"):r.close()
                r.release_conn()
    except Problem: raise
    except Exception: raise Problem("Upstream unavailable or invalid JSON.",502,"UPSTREAM_ERROR")

def transform(data,st):
    try: validate_json_tree(data)
    except Problem: raise Problem("Upstream/static JSON is too complex or invalid.",502,"RESPONSE_COMPLEXITY")
    remaining=st["max_payload_kb"]*1024
    def spend(n):
        nonlocal remaining
        remaining-=n
        require(remaining>=0,"Response expansion exceeds aggregate payload budget.",502,"RESPONSE_SIZE")
    def walk(x):
        if isinstance(x,str):
            for find,replacement in st["replace"]:
                # Check BEFORE allocating a replacement; reserve one total budget across ALL values.
                predicted=len(x.encode())+x.count(find)*(len(replacement.encode())-len(find.encode()))
                require(predicted<=remaining,"Response replacement exceeds aggregate payload budget.",502,"RESPONSE_SIZE")
                x=x.replace(find,replacement)
            spend(len(x.encode())+2); return x
        if isinstance(x,list):
            spend(2+len(x)); return [walk(v) for v in x]
        if isinstance(x,dict):
            spend(2+len(x)); result={}
            for k,v in x.items(): spend(len(k.encode())+3); result[k]=walk(v)
            return result
        spend(len(json.dumps(x))); return x
    data=walk(data)
    if st["inject"]:
        data={**data,**st["inject"]} if isinstance(data,dict) else {"result":data,**st["inject"]}
    return data

def reserve_call(s,aid,key,query,header_authenticated=False):
    a=s["apis"].get(aid); st=s["settings"]
    require(a is not None,"API not found.",404,"NOT_FOUND")
    require(not a.get('header_only') or header_authenticated,'Use the X-API-Key or Bearer header. Query-key links are disabled for this endpoint.',401,'HEADER_KEY_REQUIRED')
    require((a["public"] and not a.get("is_trial")) or (bool(key) and hmac.compare_digest(a["key_hash"],digest(key))),st["error_key"],401,"INVALID_KEY")
    require(not s["users"].get(a["owner"],{}).get("blocked",True),"API owner suspended.",403,"OWNER_BLOCKED")
    require(not s["users"].get(a["owner"],{}).get("wallet_hold"),"Owner wallet on hold. Contact payment support.",403,"WALLET_HOLD")
    if a.get('is_trial'):
        require(not a.get('trial_invalidated'),'Restored trial keys are invalidated. Create a paid API.',403,'TRIAL_RESTORED')
        require(st['trial_enabled'],'Trials are disabled by the owner.',403,'TRIAL_DISABLED')
        require(now()<a['trial_deadline'],'The API trial has expired. Choose a paid plan.',403,'TRIAL_EXPIRED')
        require(a['calls']<a['trial_limit'],'The total trial request budget is exhausted. It does not reset at midnight.',429,'TRIAL_LIMIT')
    require(a["active"],"API paused.",403,"INACTIVE")
    require(a["expires"]>now(),st["error_expired"],403,"EXPIRED")
    src=a if a["mode"]!="catalog" else s["catalog"].get(a.get("catalog_id"))
    require(src and src.get("enabled",True),"Catalogue source unavailable.",503,"SOURCE_UNAVAILABLE")
    if a.get('is_trial'):require(src.get('trial_enabled',False),'This source no longer allows trial access.',403,'TRIAL_DISABLED')
    value=query.get(src.get("param","value"),"")
    if src["mode"] in ("proxy","validation"): require(isinstance(value,str) and 0<len(value)<=1000,"Missing/invalid lookup parameter.",400,"MISSING_PARAM")
    minute=now()//60
    if a.get("minute")!=minute: a["minute"]=minute; a["minute_used"]=0
    if a.get("day")!=utc_day(): a["day"]=utc_day(); a["used"]=0
    require(a["minute_used"]<a["rpm"],"Requests per minute exceeded.",429,"RATE_LIMIT")
    require(a["used"]<a["daily"],st["error_daily"],429,"DAILY_LIMIT")
    require(not a.get('total_limit') or a['calls']<a['total_limit'],'Your plan total budget is exhausted. Renew or buy another plan.',429,'PLAN_TOTAL_LIMIT')
    s["users"][a["owner"]]["last_api_active"]=now()
    a["minute_used"]+=1; a["used"]+=1; a["calls"]+=1
    day_counter(a,'calls');day_counter(s['system'],'calls')
    if a.get('is_trial'):
        if a['calls']>=a['trial_limit']:quota_notice(s,a,'Trial quota reached')
        elif a['calls']*100>=a['trial_limit']*st['quota_warn_percent']:quota_notice(s,a,'Trial quota nearly used')
    elif a['used']>=a['daily']:quota_notice(s,a,'Daily quota reached')
    elif a['used']*100>=a['daily']*st['quota_warn_percent']:quota_notice(s,a,'Quota nearly used')
    return copy.deepcopy((a,src,st,value))

def redact_provider_credentials(data,source):
    url=source.get('url','');parts=urllib.parse.urlsplit(url)
    names={'key','api_key','apikey','token','access_token','secret','password','authorization'}
    secrets_to_hide={v for k,v in urllib.parse.parse_qsl(parts.query) if k.lower() in names and v}
    secrets_to_hide.update({url,parts.scheme+'://'+parts.netloc})
    secrets_to_hide.discard('')
    def clean(value):
        if isinstance(value,dict):return {k:('[redacted]' if k.lower() in names else clean(v)) for k,v in value.items()}
        if isinstance(value,list):return [clean(v) for v in value]
        if isinstance(value,str):
            for secret in sorted(secrets_to_hide,key=len,reverse=True):
                if value==secret:value='[redacted]'
                elif len(secret)>4:value=value.replace(secret,'[redacted]').replace(urllib.parse.quote(secret,safe=''),'[redacted]')
        return value
    return clean(data)

def record_call_state(s,aid,ok,ms):
    a=s["apis"].get(aid)
    if not a: return
    day_counter(a,'ok' if ok else 'errors');day_counter(s['system'],'ok' if ok else 'errors')
    if not ok:
        a["errors"]+=1
        if a.get("last_error_notice",0)+300<now():
            a["last_error_notice"]=now()
            audit(s,"api","upstream.failed",aid)
            soft_message(s,a["owner"],"*⚠️ API error*\n"+md(a["name"]+": an upstream attempt failed. Quota was consumed. No query data is logged."))
            notify_admins(s,"*API error*\n"+code(aid)+"\n"+md("An authenticated upstream attempt failed. Check API history. Notifications throttled to one per API every 5 minutes."))
    a["history"]=(a.get("history",[])+[{"t":now(),"ok":ok,"ms":ms}])[-30:]

def record_call(aid,ok,ms):
    store.tx(lambda s:record_call_state(s,aid,ok,ms))

def reserve_with_local_result(s,aid,key,query,header_authenticated):
    a,src,st,value=reserve_call(s,aid,key,query,header_authenticated)
    local=None
    if v415_enabled(s) and src["mode"] in ("static","validation"):
        started=time.monotonic()
        try:
            data=transform(src["data"] if src["mode"]=="static" else validation_result(src["validator"],value),st)
            require(len(json.dumps(data,ensure_ascii=False).encode())<=st["max_payload_kb"]*1024,"Transformed response exceeds payload limit.",502,"RESPONSE_SIZE")
            local={"data":data,"error":None}
        except Problem as exc:local={"data":None,"error":exc}
        record_call_state(s,aid,local["error"] is None,int((time.monotonic()-started)*1000))
    return a,src,st,value,local

@app.route("/api/<aid>",methods=["GET","OPTIONS","HEAD"])
def invoke(aid):
    if request.method=="OPTIONS": return "",204
    if request.method=="HEAD": return "",200  # capability probe, no quota use
    require(store is not None,"Service is not configured.",503,"NOT_CONFIGURED")
    require(bool(re.fullmatch(r"api_[0-9a-f]{16}",aid)),"API not found.",404,"NOT_FOUND")
    key=request.headers.get("X-API-Key","")
    if request.headers.get("Authorization","").startswith("Bearer "): key=request.headers["Authorization"][7:]
    # Query keys supported for compatibility. Header authentication avoids URL log leakage.
    header_authenticated=bool(key)
    key=key or request.args.get("key","")
    require(len(key)<=128,"Invalid API key.",401,"INVALID_KEY")
    started=time.monotonic();g.api_started=started;g.api_timings={}
    try:a,src,st,value,local=store.tx(lambda s:reserve_with_local_result(s,aid,key,request.args,header_authenticated))
    except Problem as exc:
        if exc.code in ('DAILY_LIMIT','EXPIRED','RATE_LIMIT','SOURCE_UNAVAILABLE','TRIAL_EXPIRED','TRIAL_LIMIT','TRIAL_DISABLED'):
            try:store.tx(lambda s:guard_notice(s,aid,key,exc.code))
            except Exception:LOG.warning('Warning telemetry unavailable')
        raise
    g.api_timings["database"]=round((time.monotonic()-started)*1000,2)
    t=time.monotonic(); ok=False
    try:
        if local and local["error"]:raise local["error"]
        data=local["data"] if local else src["data"] if src["mode"]=="static" else validation_result(src["validator"],value) if src["mode"]=="validation" else fetch_source(src["url"],src["param"],value,st["allowed_hosts"],st["max_payload_kb"]*1024)
        if not local:data=transform(data,st)
        if src["mode"]=="proxy":data=redact_provider_credentials(data,src)
        require(len(json.dumps(data,ensure_ascii=False).encode())<=st["max_payload_kb"]*1024,"Transformed response exceeds payload limit.",502,"RESPONSE_SIZE")
        ok=True
        return jsonify(ok=True,data=data,expires=iso(a["expires"]),daily_limit=a["daily"],daily_used=a["used"],daily_remaining=max(0,a["daily"]-a["used"]),total_calls=a["calls"],plan_name=a.get("plan_snapshot",{}).get("name",""),total_limit=a.get("total_limit",0),total_remaining=max(0,a["total_limit"]-a["calls"]) if a.get("total_limit") else None,reset="No reset: total trial budget" if a.get("is_trial") else "00:00 UTC",**({"plan":"trial","trial_limit":a["trial_limit"],"trial_remaining":max(0,a["trial_limit"]-a["calls"]),"trial_expires":iso(a["trial_deadline"])} if a.get("is_trial") else {}))
    finally:
        g.api_timings["compute"]=round((time.monotonic()-t)*1000,2)
        metrics_started=time.monotonic()
        try:
            if not local:record_call(aid,ok,int((time.monotonic()-t)*1000))
        except Exception: LOG.warning("Call telemetry write failed")
        g.api_timings["telemetry"]=round((time.monotonic()-metrics_started)*1000,2)

@app.errorhandler(Problem)
def error_problem(e):
    security_http(e.status,e.code)
    response=jsonify(ok=False,error=e.code,message=e.message); response.status_code=e.status
    if e.code in ("RATE_LIMIT","HTTP_RATE_LIMIT"): response.headers["Retry-After"]=str(60-now()%60)
    if e.code=="DAILY_LIMIT": response.headers["Retry-After"]=str(86400-now()%86400)
    return response
@app.errorhandler(Exception)
def unexpected(e):
    if isinstance(e,HTTPException):
        security_http(e.code);return jsonify(ok=False,error=e.name,message=e.description),e.code
    security_http(503)
    LOG.error("Request failed (%s)",type(e).__name__)
    return jsonify(ok=False,error="SERVICE_ERROR",message="Request could not be completed. Check server/database availability."),503
@app.after_request
def headers(r):
    r.headers["Cache-Control"]="no-store"; r.headers["X-Content-Type-Options"]="nosniff"
    r.headers["Referrer-Policy"]="no-referrer"
    nonce=getattr(g,"csp_nonce","")
    r.headers["Content-Security-Policy"]=("default-src 'self'; script-src 'nonce-"+nonce+"'; "
        "style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self' https://identitytoolkit.googleapis.com; "
        "object-src 'none'; base-uri 'none'; form-action 'self'; "+("frame-ancestors 'none'" if not DEMO else "frame-ancestors *"))
    r.headers["Permissions-Policy"]="camera=(), microphone=(), geolocation=()"
    if not DEMO:
        r.headers["X-Frame-Options"]="DENY"
        r.headers["Strict-Transport-Security"]="max-age=31536000"
    if getattr(g,"api_timings",None):
        r.headers["Server-Timing"]=", ".join(k+";dur="+str(v) for k,v in g.api_timings.items())
        r.headers["X-Response-Time-ms"]=str(round((time.monotonic()-g.api_started)*1000,2))
    if request.path.startswith("/api/"):
        r.headers["Access-Control-Allow-Origin"]="*"
        r.headers["Access-Control-Allow-Headers"]="Authorization, X-API-Key, Content-Type"
        r.headers["Access-Control-Allow-Methods"]="GET, HEAD, OPTIONS"
    return r

def prune_security_state(state):
    for user in state["users"].values():
        if user.get("flow") and user["flow"].get("t",0)+1800<=now(): user["flow"]={}
    for key in ("sessions","challenges","login_codes"):
        for sid in list(state[key]):
            if state[key][sid].get("expires",0)<=now(): del state[key][sid]

def issue_web_session(state,uid,elevated=False,expires=None):
    actor(state,uid); prune_security_state(state)
    mine=sorted((k for k,v in state["sessions"].items() if v["uid"]==str(uid)),
        key=lambda k:state["sessions"][k]["created"])
    for old in mine[:-4]: del state["sessions"][old]
    raw=secrets.token_urlsafe(32)
    state["sessions"][digest(raw)]={"uid":str(uid),"created":now(),"expires":expires or now()+28800,
        "elevated_until":now()+state["settings"].get("web_unlock_minutes",5)*60 if elevated else 0,
        "device":request.user_agent.string[:120] if has_request_context() else "Browser"}
    return raw

def adopt_session(uid,sid,login_at=None):
    session.clear(); session.update(uid=str(uid),sid=sid,login_at=login_at or now(),csrf=secrets.token_hex(24))
    session.permanent=True

def require_web_admin(state,uid):
    actor(state,uid)
    require(is_admin(uid,state),'This website is for admins only. Use the Telegram bot for trials, APIs, wallet and support.',403,'ADMIN_WEB_ONLY')

def check_web_session(state,uid,elevated=False):
    require_web_admin(state,uid)
    record=state["sessions"].get(digest(session.get("sid","")))
    require(record and record["uid"]==str(uid) and record["expires"]>now(),
        "Session expired or revoked. Sign in again with Firebase or a fresh Telegram /panel code.",401,"SESSION_REVOKED")
    actor(state,uid)
    approved=has_request_context() and getattr(g,'owner_approval',{}).get('uid')==str(uid) and getattr(g,'owner_approval',{}).get('sid')==digest(session.get('sid',''))
    if elevated and not DEMO and not approved:
        require(record.get("elevated_until",0)>now(),
            ("Firebase password confirmation required. Open Security centre." if str(uid).startswith("fb:") else "Telegram confirmation required. Open Security centre, send /confirm to your bot and verify the code."),
            403,"STEP_UP_REQUIRED")
    return record

def user_tx(uid,fn,elevated=False):
    def apply(state):
        check_web_session(state,uid,elevated)
        return fn(state)
    return store.tx(apply)

def issue_confirmation(state,uid):
    actor(state,uid,admin=True); prune_security_state(state)
    old=state["challenges"].get(str(uid),{})
    require(old.get("created",0)+30<=now(),"Please wait 30 seconds before requesting a new confirmation code.",429)
    value=f"{secrets.randbelow(100000000):08d}"
    state["challenges"][str(uid)]={"hash":digest(value),"expires":now()+180,"created":now(),"attempts":0}
    audit(state,uid,"security.confirmation-issued")
    return value

def verify_confirmation(state,uid,value):
    actor(state,uid,admin=True); old_session=check_web_session(state,uid)
    challenge=state["challenges"].get(str(uid))
    if not challenge or challenge["expires"]<=now():
        state["challenges"].pop(str(uid),None); return None
    challenge["attempts"]+=1
    valid=hmac.compare_digest(challenge["hash"],digest(value))
    if not valid:
        if challenge["attempts"]>=5: del state["challenges"][str(uid)]
        return None  # caller raises AFTER commit so failed attempts really count
    del state["challenges"][str(uid)]
    del state["sessions"][digest(session["sid"])]
    sid=issue_web_session(state,uid,elevated=True,expires=old_session["expires"])
    audit(state,uid,"security.confirmed")
    return sid

def security_summary(state,uid):
    records=[{"id":k,"current":k==digest(session.get("sid","")) if has_request_context() else False,
        "device":v["device"],"created":v["created"],"expires":v["expires"]}
        for k,v in state["sessions"].items() if v["uid"]==str(uid) and v["expires"]>now()]
    current=state["sessions"].get(digest(session.get("sid","")),{}) if has_request_context() else {}
    return {"sessions":records,"elevated_until":current.get("elevated_until",0),
        "admission":"Shared Redis" if cfg("REDIS_URL") else "Per-process (local)",
        "edge_protection":"Not verified — configure hosting/CDN WAF before production",
        "host_validation":"Demo only" if DEMO else "Production host allowlist",
        "referral_review":state["settings"]["referral_approval"],"confirmation_method":"firebase" if str(uid).startswith("fb:") else "telegram"}

_FB_STATUS_CACHE={}
_FB_STATUS_LOCK=threading.RLock()
def firebase_claims(id_token):
    require(firebase_login_available() and not DEMO,'Configure Firebase Auth REST backend credentials and database first.',503)
    require(isinstance(id_token,str) and 100<=len(id_token)<=8192,"Invalid Firebase ID token.",401)
    if getattr(store,'rest_client',None):
        claims=firebase_rest_verify(id_token)
        require(firebase_shared_account_enabled() or claims['uid']!=str(cfg('FIREBASE_BACKEND_UID')),'The backend account is not a human panel administrator.',403,'ADMIN_NOT_APPROVED')
        claims['_rest_token']=id_token
    else:
        try:
            from firebase_admin import auth as fb_auth
            claims=fb_auth.verify_id_token(id_token,app=store.firebase_app,check_revoked=True,clock_skew_seconds=30)
        except Exception: raise Problem("Firebase sign-in could not be verified. Check credentials, account status and project configuration.",401,"FIREBASE_AUTH_FAILED")
    uid=str(claims.get("uid", ""))
    require(uid in FB_SUPER_UIDS | FB_ADMIN_UIDS,"This Firebase UID is not an approved administrator.",403,"ADMIN_NOT_APPROVED")
    require(claims.get("firebase",{}).get("sign_in_provider")=="password",
        "Use Firebase Email/Password sign-in for this admin panel.",401)
    auth_time=int(claims.get("auth_time",0)); expiry=int(claims.get("exp",0))
    require(now()-300<=auth_time<=now()+60 and expiry>now(),"Please sign in again with your Firebase password.",401,"FRESH_LOGIN_REQUIRED")
    with _FB_STATUS_LOCK: _FB_STATUS_CACHE.pop(uid,None)
    return claims

def register_firebase_admin(state,claims):
    uid="fb:"+claims["uid"]
    user=register(state,uid,claims.get("name") or claims.get("email") or "Firebase admin")
    user.update(active=True,auth_provider="firebase",email=str(claims.get("email",""))[:254],firebase_uid=claims["uid"])
    actor(state,uid,admin=True)
    return uid

def issue_firebase_session(state,uid,claims,elevated=False,previous_expiry=None):
    expires=min(now()+3600,int(claims["exp"]),previous_expiry or now()+3600)
    token=issue_web_session(state,uid,elevated=elevated,expires=expires)
    state["sessions"][digest(token)].update(auth_provider="firebase",firebase_auth_time=int(claims["auth_time"]))
    if getattr(store,'rest_client',None):
        raw=claims.get('_rest_token');require(isinstance(raw,str) and raw,'Fresh Firebase token required.',401)
        state['sessions'][digest(token)]['firebase_token_enc']=fernet().encrypt(raw.encode()).decode()
    return token

def check_firebase_session(uid,record):
    if not str(uid).startswith("fb:"): return
    require(record.get("auth_provider")=="firebase" and record.get("firebase_auth_time"),"Firebase login required.",401)
    raw_uid=uid[3:]
    if getattr(store,'rest_client',None):
        try:raw=fernet().decrypt(record.get('firebase_token_enc','').encode()).decode()
        except Exception:raise Problem('Firebase session must be renewed after the REST upgrade.',401,'FIREBASE_SESSION_REVOKED') from None
        cache_key=(raw_uid,digest(raw))
        with _FB_STATUS_LOCK:
            status=_FB_STATUS_CACHE.get(cache_key)
            if not status or status['until']<=now():
                claims=firebase_rest_verify(raw,raw_uid)
                require(claims['auth_time']==record['firebase_auth_time'],'Firebase session identity changed.',401)
                status={'disabled':False,'valid_after':claims['_valid_after'],'until':min(now()+60,claims['exp'])}
                if len(_FB_STATUS_CACHE)>=512:_FB_STATUS_CACHE.clear()
                _FB_STATUS_CACHE[cache_key]=status
        require(record['firebase_auth_time']*1000>=status['valid_after'],'Firebase session revoked.',401,'FIREBASE_SESSION_REVOKED')
        return
    # Revocation/disable checks are cached for at most 60 seconds, per process; failures close access.
    with _FB_STATUS_LOCK:
        status=_FB_STATUS_CACHE.get(raw_uid)
        if not status or status["until"]<=now():
            try:
                from firebase_admin import auth as fb_auth
                user=fb_auth.get_user(raw_uid,app=store.firebase_app)
                status={"disabled":user.disabled,"valid_after":user.tokens_valid_after_timestamp,"until":now()+60}
            except Exception: raise Problem("Firebase account status could not be checked. Retry shortly.",503,"FIREBASE_UNAVAILABLE")
            if len(_FB_STATUS_CACHE)>=512: _FB_STATUS_CACHE.clear()
            _FB_STATUS_CACHE[raw_uid]=status
    require(not status["disabled"] and record["firebase_auth_time"]*1000>=status["valid_after"],
        "Firebase account disabled or credentials revoked. Sign in again.",401,"FIREBASE_SESSION_REVOKED")

@app.post("/login/firebase")
def firebase_login_route():
    check_csrf(); claims=firebase_claims(body().get("id_token"))
    def enter(state):
        uid=register_firebase_admin(state,claims)
        if session.get("sid"): state["sessions"].pop(digest(session["sid"]),None)
        sid=issue_firebase_session(state,uid,claims)
        audit(state,uid,"firebase.login")
        return uid,sid
    uid,sid=store.tx(enter); adopt_session(uid,sid)
    return jsonify(ok=True,message="Firebase admin signed in.")

def protected(admin=False,superonly=False,elevated=False):
    def deco(fn):
        @wraps(fn)
        def wrapped(*a,**kw):
            require(store is not None,"Finish server setup first.",503)
            uid=session.get("uid"); require(bool(uid),"Sign in with Firebase admin credentials or a Telegram panel code first.",401)
            require(session.get("login_at",0)+28800>now(),"Session expired.",401)
            state=store.read(); actor(state,uid,admin,superonly)
            approval_needed=web_approval_required(state,uid)
            record=check_web_session(state,uid,elevated and not approval_needed);check_firebase_session(uid,record)
            g.security_actor=str(uid)
            if approval_needed or request.method not in ("GET","HEAD","OPTIONS"):check_csrf()
            if approval_needed:
                pending=authorize_web_approval(str(uid))
                if pending is not None:return pending
            try:
                result=fn(str(uid),*a,**kw)
            except Exception:
                if getattr(g,'owner_approval',None):store.tx(lambda s:s['approvals'].get(g.owner_approval['id'],{}).update(status='failed'))
                raise
            if getattr(g,'owner_approval',None):store.tx(lambda s:s['approvals'].get(g.owner_approval['id'],{}).update(status='completed'))
            return result
        return wrapped
    return deco

def check_csrf():
    supplied=request.headers.get("X-CSRF-Token") or request.form.get("csrf","")
    require(bool(supplied) and hmac.compare_digest(str(session.get("csrf","")),supplied),"Refresh the page; CSRF token is invalid.",403)
def body():
    d=request.get_json(silent=True); require(isinstance(d,dict),"Valid JSON object required; duplicate keys/non-finite numbers are rejected."); validate_json_tree(d); return d

@app.get("/health")
def health(): return jsonify(ok=store is not None,version=VERSION,mode="demo" if DEMO else "production",build="PRIVATE-CHAT-4171"),200 if store else 503
@app.get("/manage/state")
@protected()
def state_route(uid): return jsonify(public_state(store.read(),uid))
@app.post("/manage/activate")
@protected()
def activate_route(uid): return jsonify(message=user_tx(uid,lambda s:activate(s,uid)))
@app.post("/manage/apis")
@protected()
def create_route(uid):
    d=body(); return jsonify(user_tx(uid,lambda s:create_api(s,uid,d)))
@app.post("/manage/apis/<aid>/<action>")
@protected()
def api_action_route(uid,aid,action):
    d=body()
    def change(state):
        a=owned(state,uid,aid)
        if (is_admin(uid,state) and a["owner"]!=str(uid)) or (action=="edit" and d.get("public") is True):
            check_web_session(state,uid,elevated=True)
        return api_action(state,uid,aid,action,d)
    return jsonify(user_tx(uid,change))
@app.post('/manage/trial')
@protected()
def trial_route(uid):
    raise Problem('Trial claims are available only in the Telegram bot. Use /trial or /demo.',403,'BOT_ONLY')


@app.post("/manage/admin/<kind>")
@protected(admin=True)
def admin_route(uid,kind):
    d=body()
    sensitive=kind in ("settings","catalog","kv","redeem","credit") or (kind=="user" and (any(k in d for k in ("role","coins","diamonds","delete")) or d.get("blocked") is False))
    return jsonify(user_tx(uid,lambda s:admin_action(s,uid,kind,d),elevated=sensitive))
@app.post('/manage/notifications/read')
@protected(admin=True)
def notification_read_route(uid):
    return jsonify(user_tx(uid,lambda s:s['users'][uid].update(notification_seen=now(),notification_seen_ids=list(s.get('admin_notifications',{}))) or {'ok':True}))

@app.post("/logout")
def logout_route():
    check_csrf()
    if store and session.get("sid"): store.tx(lambda s:s["sessions"].pop(digest(session["sid"]),None))
    session.clear(); return jsonify(ok=True)

@app.post("/manage/security/firebase")
@protected(admin=True)
def firebase_confirm_route(uid):
    require(uid.startswith("fb:"),"This account uses Telegram confirmation, not Firebase.",403)
    claims=firebase_claims(body().get("id_token"))
    require("fb:"+claims["uid"]==uid,"Confirm with the same Firebase administrator account.",403)
    def confirm(state):
        old=check_web_session(state,uid)
        state["sessions"].pop(digest(session["sid"]),None)
        sid=issue_firebase_session(state,uid,claims,elevated=True,previous_expiry=old["expires"])
        audit(state,uid,"firebase.confirmed")
        return sid
    sid=user_tx(uid,confirm); login_at=session.get("login_at",now()); adopt_session(uid,sid,login_at)
    return jsonify(ok=True,message="Firebase password confirmed. Sensitive actions unlocked for the configured window.")

@app.post("/manage/security/verify")
@protected(admin=True)
def verify_route(uid):
    value=str(body().get("code",""))
    require(bool(re.fullmatch(r"[0-9]{8}",value)),"Enter the 8-digit code from /confirm.")
    sid=store.tx(lambda s:verify_confirmation(s,uid,value))
    require(sid is not None,"Invalid or expired confirmation code. After 5 failures, request a new code.",403,"INVALID_CONFIRMATION")
    login_at=session.get("login_at",now()); adopt_session(uid,sid,login_at)
    return jsonify(ok=True,message="Sensitive actions unlocked for the configured window. Session token rotated.")

@app.post("/manage/security/revoke")
@protected()
def revoke_route(uid):
    data=body(); target=str(data.get("id", "")); current=digest(session["sid"])
    def revoke(state):
        removed=0
        for key,value in list(state["sessions"].items()):
            if value["uid"]==str(uid) and key!=current and (target=="others" or key==target):
                del state["sessions"][key]; removed+=1
        audit(state,uid,"security.sessions-revoked",str(removed)); return removed
    count=user_tx(uid,revoke)
    return jsonify(ok=True,message=f"Signed out {count} other session(s).")

# Wallets: integer virtual units only. Payment records are never evicted for deduplication.
def integer(value,label,low=1,high=1000000):
    require(type(value) is int and low<=value<=high,f"{label}: integer {low}–{high} required.")
    return value

def economy_capacity(s):
    require(len(s['orders'])<2000,'Payment order capacity reached. Reconcile/archive to a dedicated payment datastore before growing.',503)
    require(len(json.dumps({'orders':s['orders'],'charges':s['charges'],'manual_refs':s['manual_refs']}).encode())<1500000,
        'Payment record capacity reached. Contact the owner.',503)

def wallet_change(s,uid,currency,delta,reason,reference='',allow_debt=False):
    require(currency in ('coins','diamonds'),'Invalid wallet currency.')
    u=s['users'].get(str(uid));require(u is not None,'Wallet account missing.',409)
    integer(delta,'Wallet change',-1000000000,1000000000)
    balance=u.get(currency,0)+delta
    require(-1000000000<=balance<=1000000000,'Wallet balance limit reached.',409)
    require(allow_debt or balance>=0,'Insufficient '+currency+'.',402)
    u[currency]=balance;u['wallet_hold']=u.get('coins',0)<0 or u.get('diamonds',0)<0
    k=new_id('txn_');s['ledger'][k]={'id':k,'uid':str(uid),'currency':currency,'delta':delta,'balance':balance,'reason':reason,'reference':reference[:160],'t':now()}
    # Recent wallet activity is bounded; permanent payment/order idempotency records are separate.
    while len(s['ledger'])>2000:del s['ledger'][next(iter(s['ledger']))]
    return balance

def create_redeem(s,uid,d):
    actor(s,uid,superonly=True)
    require(len(s['redeem_codes'])<500,'Redeem registry full; retain claim records and contact the owner.',409)
    coins=integer(d.get('coins'),'Coins',1,1000000);uses=integer(d.get('uses',1),'Maximum users',1,3000);days=integer(d.get('days',7),'Valid days',1,365)
    token='GIFT_'+secrets.token_urlsafe(18);h=digest(token)
    record={'id':new_id('gift_'),'coins':coins,'uses':uses,'expires':now()+days*86400,'created':now(),'enabled':True,'claims':{}}
    s['redeem_codes'][h]=record;s['system']['external_payments']=True;check_data_capacity(s);audit(s,uid,'redeem.create',record['id'])
    return {'code':token,**{k:v for k,v in record.items() if k!='claims'}}

def claim_redeem(s,uid,token):
    u=actor(s,uid);require(u.get('active') and joined(s,uid) and not u.get('wallet_hold'),'Activate, verify joins and resolve wallet holds before redeeming.',403)
    require(isinstance(token,str) and re.fullmatch(r'[A-Za-z0-9_-]{6,80}',token),'Invalid redeem code.')
    r=s['redeem_codes'].get(digest(token));require(r and r['enabled'] and r['expires']>now(),'Redeem code unavailable or expired.',409,'REDEEM_UNAVAILABLE')
    require(str(uid) not in r['claims'],'This account already redeemed that code.',409,'REDEEM_USED')
    require(len(r['claims'])<r['uses'],'Redeem code has reached its user limit.',409,'REDEEM_EXHAUSTED')
    balance=wallet_change(s,uid,'coins',r['coins'],'Redeem reward',r['id'])
    r['claims'][str(uid)]=now();s['system']['external_payments']=True;check_data_capacity(s);audit(s,uid,'redeem.claim',r['id'])
    return {'coins':r['coins'],'balance':balance}

def grant_credit(s,uid,d):
    actor(s,uid,superonly=True);target=str(d.get('uid',''));u=s['users'].get(target)
    require(u and target.isdigit() and not u.get('blocked'),'Choose a registered, unblocked Telegram user.')
    coins=integer(d.get('coins'),'Coins',1,1000000);ref=str(d.get('reference','')).strip()
    require(bool(re.fullmatch(r'[A-Za-z0-9_-]{6,64}',ref)),'Use a unique reference: 6–64 letters/digits/dash/underscore.')
    h=digest('credit:'+ref);old=s['credit_grants'].get(h)
    if old:
        require(old['uid']==target and old['coins']==coins,'Reference already belongs to another credit adjustment.',409)
        return {'message':'Already credited; no second credit.','balance':u['coins']}
    require(len(s['credit_grants'])<5000,'Credit reference registry full. Do not discard idempotency records.',409)
    balance=wallet_change(s,target,'coins',coins,'Owner credit adjustment',ref)
    s['credit_grants'][h]={'uid':target,'coins':coins,'actor':str(uid),'t':now()};s['system']['external_payments']=True
    check_data_capacity(s);audit(s,uid,'wallet.credit',target)
    soft_message(s,target,md(f'💙 Owner added {coins} coins. Balance: {balance}.'))
    return {'message':f'Credited {coins} coins to {target}.','balance':balance}

def api_price(s,source=None):
    source=source or {}
    if source.get('plans'):
        available=[p for p in source['plans'] if p.get('enabled',True)]
        if available:return 'coins',min(p['price'] for p in available)
    return source.get('billing_currency','coins'),source.get('price',s['settings']['default_api_price'])

def charge_api(s,uid,currency,price,reference):
    u=actor(s,uid);require(not u.get('wallet_hold'),'Wallet is on hold after a refund. Contact payment support.',403)
    if not is_admin(uid,s):wallet_change(s,uid,currency,-price,'API purchase / renewal',reference)

def convert_diamonds(s,uid,amount,expected_rate):
    u=actor(s,uid);require(u.get('active') and not u.get('wallet_hold'),'Activate your account or resolve the wallet hold first.',403)
    amount=integer(amount,'Diamonds',1,1000000);rate=s['settings']['diamond_coin_rate']
    require(rate>0,'Diamond conversion has not been configured.',409)
    require(expected_rate==rate,'Conversion rate changed. Refresh and confirm the new rate.',409)
    wallet_change(s,uid,'diamonds',-amount,'Convert diamonds to coins')
    wallet_change(s,uid,'coins',amount*rate,'Diamond conversion')
    return {'message':f'Converted {amount} diamonds into {amount*rate} coins.'}

def package_validate(data):
    require(isinstance(data,list) and len(data)<=20,'Use up to 20 purchase packs.')
    packs=[];seen=set()
    for p in data:
        require(isinstance(p,dict),'Invalid pack.')
        pid=p.get('id','');require(isinstance(pid,str) and re.fullmatch(r'[A-Za-z0-9_-]{1,32}',pid) and pid not in seen,'Unique pack ID required (letters, digits, dash/underscore).');seen.add(pid)
        name=p.get('name','');require(isinstance(name,str) and 1<=len(name.strip())<=60,'Pack name: 1–60 characters.')
        require(p.get('currency') in ('coins','diamonds'),'Pack currency must be coins or diamonds.')
        require(type(p.get('enabled',True)) is bool,'enabled must be boolean.')
        packs.append({'id':pid,'name':name.strip(),'currency':p['currency'],'amount':integer(p.get('amount'),'Pack units'),
            'stars':integer(p.get('stars'),'Star price',1,10000),'inr_paise':integer(p.get('inr_paise',0),'UPI paise',0,10000000),'enabled':p.get('enabled',True)})
    return packs

def new_order(s,uid,pack_id,method='stars',reference='',quote=None):
    u=actor(s,uid);require(str(uid).isdigit() and u.get('active'),'Purchases require an activated Telegram user account.',403)
    require(method in ('stars','upi'),'Invalid purchase method.')
    require(bool(s['settings']['support_username']),'Owner must configure payment support before purchases.',409)
    pack=next((p for p in s['settings']['purchase_packs'] if p['id']==pack_id and p['enabled']),None)
    require(pack is not None,'Purchase pack unavailable.',404)
    if quote is not None:
        require(isinstance(quote,dict) and all(quote.get(k)==pack[k] for k in ('currency','amount','inr_paise')),'Pack price changed. Contact support and refresh before submitting a payment reference.',409)
    require(sum(o['uid']==str(uid) and o['status']=='pending' and o['created']>now()-86400 for o in s['orders'].values())<5,'You already have 5 pending purchases. Contact support before creating more.',429)
    economy_capacity(s)
    reference=str(reference).strip()
    if method=='upi':
        require(s['settings']['support_username'] and pack['inr_paise']>0,'Manual UPI purchases are not configured.',409)
        require(bool(re.fullmatch(r'[A-Za-z0-9_-]{6,64}',reference)),'Enter the payment reference (6–64 letters/digits/dash/underscore).')
        require(digest(reference.lower()) not in s['manual_refs'],'This payment reference has already been submitted.',409)
    else:require(not DEMO,'Real Stars payments are disabled in the demo.',403)
    oid=new_id('ord_')
    o={'id':oid,'uid':str(uid),'method':method,'pack_id':pack['id'],'name':pack['name'],'currency':pack['currency'],
        'amount':pack['amount'],'stars':pack['stars'],'inr_paise':pack['inr_paise'],'status':'pending','created':now(),
        'payload':'srdark:'+oid,'reference':reference,'terms':s['settings']['payment_terms']}
    s['orders'][oid]=o
    if method=='upi':
        s['manual_refs'][digest(reference.lower())]=oid
        audit(s,uid,'payment.upi-requested',oid)
    else:
        enqueue(s,uid,'',kind='invoice',backup=oid)
        audit(s,uid,'payment.invoice-queued',oid)
    return {'id':oid,'message':'Payment reference submitted. Balance is credited only after the owner verifies the actual bank payment.' if method=='upi' else 'Stars invoice queued for your private bot chat. Balance changes only after confirmed payment.'}

def invoice_payload(o):
    return {'chat_id':int(o['uid']),'title':o['name'][:32],'description':f"{o['amount']} {o['currency']}. Virtual account balance; not Telegram Stars or cash. See /terms and /paysupport before paying.",
        'payload':o['payload'],'provider_token':'','currency':'XTR','prices':[{'label':o['name'],'amount':o['stars']}],'start_parameter':o['id']}

def find_payment_order(s,payload):
    require(isinstance(payload,str) and payload.startswith('srdark:') and len(payload)<=80,'Unknown invoice.',400)
    o=s['orders'].get(payload[7:]);require(o and o['payload']==payload and o['method']=='stars','Unknown Stars invoice.',400)
    return o

def precheckout(s,q):
    try:
        o=find_payment_order(s,q.get('invoice_payload'))
        require(str(q.get('from',{}).get('id'))==o['uid'],'This invoice belongs to another account.',403)
        actor(s,o['uid'])
        require(o['status']=='pending' and o['created']+86400>now(),'Invoice expired or already processed. Create a new invoice.',409)
        require(q.get('currency')=='XTR' and type(q.get('total_amount')) is int and q['total_amount']==o['stars'],'Invoice amount does not match.',400)
        qid=q.get('id');require(isinstance(qid,str) and 1<=len(qid)<=200,'Invalid checkout ID.')
        require(not o.get('checkout_id') or o['checkout_id']==qid,'A checkout already exists for this invoice. Contact support if it failed.',409)
        o['checkout_id']=qid;o['checkout_at']=now()
        return {'method':'answerPreCheckoutQuery','pre_checkout_query_id':qid,'ok':True}
    except Problem as e:
        return {'method':'answerPreCheckoutQuery','pre_checkout_query_id':str(q.get('id',''))[:200],'ok':False,'error_message':e.message[:200]}

def apply_payment(s,message,refund=None):
    require(bool(message.get('refunded_payment')) != bool(message.get('successful_payment')),'Exactly one payment event is required.')
    if refund is None:refund=bool(message.get('refunded_payment'))
    p=message.get('refunded_payment' if refund else 'successful_payment',{})
    o=find_payment_order(s,p.get('invoice_payload'))
    require(message.get('chat',{}).get('type')=='private' and str(message['chat']['id'])==o['uid'],'Payment account mismatch.',403)
    if not refund:require(str(message.get('from',{}).get('id'))==o['uid'],'Payment sender mismatch.',403)
    require(p.get('currency')=='XTR' and type(p.get('total_amount')) is int and p['total_amount']==o['stars'],'Payment amount mismatch.',400)
    charge=p.get('telegram_payment_charge_id');require(isinstance(charge,str) and 1<=len(charge)<=512,'Invalid charge ID.')
    previous=s['charges'].get(digest(charge))
    require(previous in (None,o['id']),'Charge already belongs to a different order.',409)
    require(not o.get('charge') or o['charge']==charge,'Different payment received for a settled invoice. Owner must reconcile and refund the extra charge.',409)
    s['charges'][digest(charge)]=o['id'];o['charge']=charge;s['system']['external_payments']=True
    if refund:
        if o['status']=='refunded':return False
        if o['status']=='paid':wallet_change(s,o['uid'],o['currency'],-o['amount'],'Stars refund',o['id'],allow_debt=True)
        # refund_pending was already debited; refunds arriving before success never grant units.
        o.update(status='refunded',refunded_at=now());audit(s,o['uid'],'payment.refunded',o['id'])
        return True
    if o['status'] in ('paid','refund_pending','refunded'):return False
    require(o['status']=='pending','Payment needs owner reconciliation.',409)
    wallet_change(s,o['uid'],o['currency'],o['amount'],'Stars purchase',o['id'])
    o.update(status='paid',paid_at=now());audit(s,o['uid'],'payment.paid',o['id'])
    if len(s['outbox'])<1900:enqueue(s,o['uid'],'*Payment received*\n'+md(f"{o['amount']} {o['currency']} added. Order: {o['id']}. Open /wallet to see your balance."))
    # A full notification queue must never discard a valid credit.
    return True

def review_upi(s,uid,oid,approve,verification):
    actor(s,uid,superonly=True);o=s['orders'].get(oid)
    require(o and o['method']=='upi','Manual payment not found.',404)
    if o['status'] in ('paid','rejected'):return {'message':'This request has already been reviewed.'}
    require(o['status']=='pending','Request cannot be reviewed.',409)
    if approve:
        require(verification=='VERIFIED','Type VERIFIED only after checking the amount/reference in your own bank account.',400)
        wallet_change(s,o['uid'],o['currency'],o['amount'],'Verified manual UPI purchase',o['id'])
        s['system']['external_payments']=True
    o.update(status='paid' if approve else 'rejected',reviewer=uid,reviewed_at=now())
    audit(s,uid,'payment.upi-'+o['status'],oid)
    return {'message':'Manual payment approved and wallet credited.' if approve else 'Payment request rejected.'}

def begin_refund(s,uid,oid):
    actor(s,uid,superonly=True);o=s['orders'].get(oid)
    require(o and o['method']=='stars' and o.get('charge'),'Paid Stars order not found.',404)
    require(o['status'] in ('paid','refund_pending','refunded'),'This order is not refundable.',409)
    if o['status']=='paid':
        wallet_change(s,o['uid'],o['currency'],-o['amount'],'Stars refund requested',oid,allow_debt=True)
        o['status']='refund_pending';audit(s,uid,'payment.refund-requested',oid)
    return copy.deepcopy(o)

@app.post('/manage/wallet/<action>')
@protected()
def wallet_route(uid,action):
    d=body()
    if action=='convert':return jsonify(user_tx(uid,lambda s:convert_diamonds(s,uid,d.get('amount'),d.get('rate'))))
    require(action in ('buy','manual'),'Unknown wallet action.',404)
    result=user_tx(uid,lambda s:new_order(s,uid,d.get('pack_id'),'stars' if action=='buy' else 'upi',d.get('reference',''),d.get('quote')))
    if action=='buy':drain(1)
    return jsonify(result)

@app.post('/manage/payments/<oid>/<action>')
@protected(superonly=True,elevated=True)
def payment_admin_route(uid,oid,action):
    d=body()
    if action in ('approve','reject'):
        return jsonify(user_tx(uid,lambda s:review_upi(s,uid,oid,action=='approve',d.get('verification')),elevated=True))
    require(action=='refund','Unknown payment action.',404)
    require(not DEMO,'Real refunds are disabled in the demo.',403)
    order=user_tx(uid,lambda s:begin_refund(s,uid,oid),elevated=True)
    if order['status']!='refunded':
        result=tg('refundStarPayment',{'user_id':int(order['uid']),'telegram_payment_charge_id':order['charge']})
        require(result is True,'Refund confirmation unavailable. Order remains refund_pending; reconcile with Telegram.',502)
        def finish(s):
            o=s['orders'][oid];o.update(status='refunded',refunded_at=now());audit(s,uid,'payment.refunded',oid)
        store.tx(finish)
    return jsonify(message='Stars refund confirmed. Any negative wallet balance holds API access until resolved.')


# Automatic announcements enroll on a real /start. Historical exclusions, blocks and caps apply.
ENGAGEMENT_KEYS={'welcome_dashboard','welcome_mode','welcome_caption','welcome_links','campaigns_enabled','campaign_timezone','delivery_start_hour','delivery_end_hour','campaign_daily_cap','campaign_gap_hours'}

def text_units(value):
    try:return len(value.encode('utf-16-le'))//2
    except (AttributeError,UnicodeError):raise Problem('Text contains invalid Unicode.')

def clip_text(value,units):
    return str(value).encode('utf-16-le').__getitem__(slice(0,units*2)).decode('utf-16-le',errors='ignore')

def marketing_text(value,label,limit=700):
    require(isinstance(value,str) and 1<=text_units(value.strip())<=limit,label+f': 1–{limit} text units required.')
    require(not any(ord(c)<32 and c not in '\n\t' for c in value),'Control characters are not allowed.')
    return value.strip()

def marketing_links(links):
    require(isinstance(links,list) and len(links)<=4,'Use at most 4 link buttons.')
    out=[]
    for item in links:
        require(isinstance(item,dict),'Each button needs label and url.')
        label=marketing_text(item.get('label'),'Button label',40);url=item.get('url','')
        require(isinstance(url,str) and text_units(url)<=500 and not any(ord(c)<=32 for c in url),'Invalid button URL.')
        p=urllib.parse.urlsplit(url)
        require(p.scheme=='https' and p.hostname and not p.username and not p.password,'Buttons must use HTTPS links without credentials.')
        out.append({'label':label,'url':url})
    return out

def engagement_settings(state,uid,data):
    actor(state,uid,admin=True)
    require(set(data)<=ENGAGEMENT_KEYS|{'remove_photo','remove_video'},'Unknown engagement setting.')
    st=state['settings'];change={}
    for k in ('welcome_dashboard','welcome_caption','welcome_links','campaigns_enabled','campaign_timezone'):
        if k not in data:continue
        value=data[k]
        if k=='welcome_caption':
            if data.get('welcome_mode',st.get('welcome_mode'))=='entities':require(value==st['welcome_caption'],'Captured formatting must be edited through /setmessage.')
            else:value=marketing_text(value,'Welcome caption')
        elif k=='welcome_links':value=marketing_links(value)
        elif k in ('campaigns_enabled','welcome_dashboard'):require(type(value) is bool,'Switch must be boolean.')
        else:
            require(isinstance(value,str) and len(value)<=64,'Invalid IANA timezone.')
            try:ZoneInfo(value)
            except (ValueError,KeyError):raise Problem('Unknown timezone; use Asia/Kolkata, UTC, etc.')
        change[k]=value
    for k,low,high in [('delivery_start_hour',0,23),('delivery_end_hour',1,24),('campaign_daily_cap',1,3),('campaign_gap_hours',6,168)]:
        if k in data:change[k]=integer(data[k],k,low,high)
    require(change.get('delivery_start_hour',st['delivery_start_hour'])<change.get('delivery_end_hour',st['delivery_end_hour']),
        'Delivery start hour must be earlier than end hour. Overnight windows are not supported.')
    if 'remove_photo' in data:
        require(type(data['remove_photo']) is bool,'remove_photo must be boolean.')
        if data['remove_photo']:change['welcome_photo']=''
    if 'remove_video' in data:
        require(type(data['remove_video']) is bool,'remove_video must be boolean.')
        if data['remove_video']:change['welcome_video']=''
    mode=data.get('welcome_mode',st.get('welcome_mode','plain'))
    require(mode in ('plain','markdown','entities'),'Invalid welcome format.')
    value=change.get('welcome_caption',st['welcome_caption'])
    if mode=='entities':require(value==st['welcome_caption'],'Edit captured formatted text using /setmessage, or choose Plain/Markdown.')
    formatted_template(value,mode,st.get('welcome_entities',[]))
    change['welcome_mode']=mode
    if mode!='entities':change['welcome_entities']=[]
    st.update(change)
    if 'welcome_photo' in change:
        for c in state['campaigns'].values():
            if c['use_welcome_photo']:cancel_promos(state,cid=c['id']);c['run']=None
    if not st['campaigns_enabled']:
        cancel_promos(state)
        for c in state['campaigns'].values():c['run']=None
    check_data_capacity(state);audit(state,uid,'engagement.settings',', '.join(change))
    return {'message':'Welcome and delivery policy saved. Bot-start eligibility, historical exclusions and frequency limits always apply.'}

def delivery_window(st,at=None):
    t=now() if at is None else at;zone=ZoneInfo(st['campaign_timezone']);dt=datetime.fromtimestamp(t,zone)
    start=dt.replace(hour=st['delivery_start_hour'],minute=0,second=0,microsecond=0)
    end=dt.replace(hour=0,minute=0,second=0,microsecond=0)+timedelta(hours=st['delivery_end_hour'])
    if dt<start:return False,int(start.timestamp()),dt.date().isoformat()
    if dt>=end:return False,int((start+timedelta(days=1)).timestamp()),dt.date().isoformat()
    return True,t,dt.date().isoformat()

def random_due(st,c,after=None):
    base=now() if after is None else after
    lo=c['min_hours']*3600;hi=c['max_hours']*3600
    candidate=base+lo+secrets.randbelow(hi-lo+1)
    allowed,next_open,_=delivery_window(st,candidate)
    if allowed:return candidate
    span=(st['delivery_end_hour']-st['delivery_start_hour'])*3600
    return next_open+secrets.randbelow(span)

def subscriber(u):
    return str(u.get('id','')).isdigit() and u.get('telegram_started',False) and u.get('updates_on',False) and not u.get('broadcast_hold',False) and not u.get('blocked') and not u.get('telegram_blocked')

def last_activity(u):return max(u.get('last_active',u.get('joined',0)),u.get('last_api_active',0))

def event_seen(u,c,fp):
    saved=u.get('campaign_events',{}).get(c['id'])
    if c['trigger']=='expiry':return isinstance(saved,dict) and saved.get(fp.split(':')[1])==digest(fp)[:24]
    return saved==digest(fp)[:24]

def event_for(s,c,u,expected=None):
    if c['trigger']=='once':return ('once:'+c['id']+':'+str(c['revision']),{})
    if c['trigger']=='random':return ('run:'+c.get('run',{}).get('id',''),{}) if c.get('run') else (None,{})
    if c['trigger']=='inactive':
        last=last_activity(u)
        return ('inactive:'+str(last),{}) if last+c['threshold_days']*86400<=now() else (None,{})
    candidates=sorted((a for a in s['apis'].values() if a['owner']==u['id'] and a['active'] and now()-86400<a['expires']<=now()+c['threshold_days']*86400),key=lambda a:a['expires'])
    for a in candidates:
        fp='expiry:'+a['id']+':'+str(a['expires'])
        if expected and digest(fp)[:24]!=expected:continue
        if not expected and event_seen(u,c,fp):continue
        expires=datetime.fromtimestamp(a['expires'],ZoneInfo(s['settings']['campaign_timezone'])).strftime('%d %b %Y %H:%M %Z')
        return fp,{'api_name':a['name'],'expires':expires,'days_left':str(max(0,math.ceil((a['expires']-now())/86400))),'status':'expired' if a['expires']<=now() else 'expiring'}
    return None,{}

def render_marketing(template,u,st,extra=None):
    values={'name':u['name'],'coins':str(u.get('coins',0)),'diamonds':str(u.get('diamonds',0)),
        'referral_reward':str(st['referral_reward']),'api_price':str(st['default_api_price']),**(extra or {})}
    # One pass, explicit placeholders only; no eval/format traversal, no nested replacement.
    return clip_text(re.sub(r'\{([a-z_]+)\}',lambda m:str(values.get(m[1],m[0])),template),700)

def link_rows(links):return [[btn(item['label'],url=item['url'])] for item in links]

def welcome_enqueue(s,uid,preview=False,keyboard=None):
    if simple_ui(s) and not preview:
        text,rows=simple_home(s,uid);key=enqueue(s,uid,text,keyboard if keyboard is not None else rows);nav_job(s,key,uid);return key
    u=s['users'][uid];st=s['settings']
    if focused_ui(s) and not preview and valid_nav(u.get('bot_nav')):
        text,rows=menu(s,uid);key=enqueue(s,uid,text,keyboard or rows);nav_job(s,key,uid);return key
    text=dashboard_text(s,uid) if st.get('welcome_dashboard') else md(render_marketing(st['welcome_caption'],u,st))
    rows=keyboard if keyboard is not None else link_rows(st['welcome_links'])+menu(s,uid)[1]
    key=enqueue(s,uid,text,rows,kind='photo' if st['welcome_photo'] else 'message')
    s['outbox'][key]['priority']=-1
    if preview:s['outbox'][key]['explicit_preview']=True
    if st['welcome_photo']:s['outbox'][key]['photo']=st['welcome_photo']
    if st.get('welcome_video'):
        s['outbox'][key].pop('photo',None);s['outbox'][key].update(video=st['welcome_video'],kind='message')
    if not st.get('welcome_dashboard') and st.get('welcome_mode','plain')!='plain':
        attach_rich(s,key,st['welcome_caption'],st['welcome_mode'],st.get('welcome_entities',[]),u)
    # Decorative, requested /start reply only: never attached to paid events or campaigns.
    if (st.get('welcome_sticker') and len(s['outbox'])<1900
        and u.get('last_welcome_sticker_at',0)+60<=now()
        and not any(v.get('kind')=='sticker' and v['chat']==uid for v in s['outbox'].values())):
        sk=enqueue(s,uid,'',kind='sticker')
        s['outbox'][sk].update(sticker=st['welcome_sticker'],after=key,priority=-1,expires=now()+300)
        u['last_welcome_sticker_at']=now()
    return key

def clear_welcome_stickers(s):
    for key,item in list(s['outbox'].items()):
        if item.get('kind')=='sticker':del s['outbox'][key]

def save_welcome_sticker(s,uid,message):
    u=actor(s,uid,admin=True);flow=u.get('flow',{})
    require(flow.get('step')=='welcome_sticker' and flow.get('t',0)+600>now(),
            'Sticker setup expired. Send /setsticker again.')
    sticker=message.get('sticker')
    require(isinstance(sticker,dict) and sticker.get('type','regular')=='regular',
            'Send a regular Telegram sticker, not a mask, custom emoji or document.')
    file_id=sticker.get('file_id','')
    require(isinstance(file_id,str) and re.fullmatch(r'[A-Za-z0-9_-]{10,512}',file_id),
            'Invalid Telegram sticker identifier.')
    info={'format':'video' if sticker.get('is_video') else 'animated' if sticker.get('is_animated') else 'static',
          'premium':bool(sticker.get('premium_animation'))}
    clear_welcome_stickers(s)
    s['settings'].update(welcome_sticker=file_id,welcome_sticker_info=info)
    u['flow']={};check_data_capacity(s);audit(s,uid,'welcome.sticker',info['format'])
    return 'Welcome sticker saved ('+info['format']+'). Send /start to preview. Premium effects depend on Telegram; they are not unlocked by this code. /removesticker disables it.'

def bot_design(s,uid):
    actor(s,uid,admin=True);st=s['settings'];info=st.get('welcome_sticker_info',{})
    text=bot_title(s,'Bot appearance')+'\n\n'+md('Text: '+st['bot_text_style']+'\nSticker: '+(info.get('format','selected') if st.get('welcome_sticker') else 'not selected'))
    text+='\n\n'+md('Blue = navigation · Green = positive actions · Red = destructive actions. Small-caps are decorative Unicode, not a custom font or smaller font size. Classic headings are available for readability.')
    text+='\n\n_'+md('Choose a dynamic dashboard, custom formatted caption, photo or video. The requested dashboard upgrade removes the separate welcome sticker.')+'_'
    rows=[[btn('Compact headings','style:compact','success'),btn('Classic headings','style:classic')],
          [btn('Dashboard welcome','dashboard','success'),btn('Set welcome video','setvideo')],
          [btn('Set welcome photo','setwelcome'),btn('Preview welcome','previewwelcome')],
          [btn('Admin','admin'),btn('Home','home')]]
    if role(uid,s)=='superadmin':rows.insert(-1,[btn('💙 Button emoji icons','buttonicons')])
    return text,rows

def save_welcome_photo(s,uid,message):
    u=actor(s,uid,admin=True);flow=u.get('flow',{})
    require(flow.get('step')=='welcome_photo' and flow.get('t',0)+600>now(),'Photo setup expired. Send /setwelcome again.')
    photos=message.get('photo');require(isinstance(photos,list) and photos,'Send the image as a Telegram photo, not as a document.')
    file_id=photos[-1].get('file_id','');require(isinstance(file_id,str) and re.fullmatch(r'[A-Za-z0-9_-]{10,512}',file_id),'Invalid Telegram photo identifier.')
    s['settings']['welcome_photo']=file_id;s['settings']['welcome_video']=''
    if message.get('caption'):s['settings'].update(welcome_caption=marketing_text(message['caption'],'Photo caption'),welcome_mode='plain',welcome_entities=[],welcome_dashboard=False)
    for c in s['campaigns'].values():
        if c['use_welcome_photo']:cancel_promos(s,cid=c['id']);c['run']=None
    u['flow']={};audit(s,uid,'welcome.photo','Photo captured through authenticated private bot chat')
    return 'Welcome image saved. Its optional caption is saved as plain text. Send /start to preview, or edit Welcome & Broadcast in the panel.'

def drop_promo(s,key,reason='skipped'):
    v=s['outbox'].pop(key,None)
    if not v:return
    u=s['users'].get(v['chat']);c=s['campaigns'].get(v.get('campaign_id'))
    if u and u.get('promo_pending')==key:u['promo_pending']=''
    if c:c[reason]=c.get(reason,0)+1

def cancel_promos(s,uid=None,cid=None):
    for k,v in list(s['outbox'].items()):
        if v.get('kind')!='engagement' or (uid and v['chat']!=uid) or (cid and v.get('campaign_id')!=cid):continue
        if v.get('lease',0)>now():v['cancelled']=True
        else:drop_promo(s,k)

def updates_preference(s,uid,enabled):
    u=actor(s,uid);require(str(uid).isdigit() and u.get('telegram_started'),'Open /start in a private Telegram chat first.',403)
    require(type(enabled) is bool,'Choose whether to subscribe.')
    u['updates_on']=enabled;u['broadcast_hold']=not enabled
    if not enabled:cancel_promos(s,uid=uid)
    audit(s,uid,'updates.opt-in' if enabled else 'updates.opt-out')
    return {'message':'Broadcast audience preference saved.' if enabled else 'Broadcasts and optional reminders stopped. Requested replies, invoices and security messages are unaffected. Previous disabled-message preferences stay disabled.'}

def save_campaign(s,uid,d):
    actor(s,uid,admin=True);cid=str(d.get('id') or new_id('camp_'))
    require(bool(re.fullmatch(r'camp_[0-9a-f]{16}',cid)),'Invalid campaign ID.')
    old=s['campaigns'].get(cid)
    require(old is not None or len(s['campaigns'])<12,'Maximum 12 campaigns. Delete an unused campaign before adding another.',409)
    name=marketing_text(d.get('name'),'Campaign name',60)
    if d.get('text_mode',(old or {}).get('text_mode','plain'))=='entities':
        require(old and d.get('text')==old['text'],'Update captured campaign text through /setcampaign.');text=old['text']
    else:text=marketing_text(d.get('text'),'Campaign message')
    trigger=d.get('trigger','random');require(trigger in ('random','inactive','expiry','once'),'Choose once, random, inactive or expiry.')
    lo=integer(d.get('min_hours',24),'Minimum interval',6,168);hi=integer(d.get('max_hours',24),'Maximum interval',lo,336)
    days=integer(d.get('threshold_days',3),'Threshold days',1,90 if trigger!='expiry' else 14)
    enabled=d.get('enabled',False);photo=d.get('use_welcome_photo',False)
    require(type(enabled) is bool and type(photo) is bool,'Campaign switches must be boolean.')
    if photo:require(bool(s['settings']['welcome_photo']),'Upload a welcome photo with /setwelcome first.')
    cancel_promos(s,cid=cid)
    c={'id':cid,'name':name,'text':text,'links':marketing_links(d.get('links',[])),'trigger':trigger,'min_hours':lo,'max_hours':hi,
        'threshold_days':days,'enabled':enabled,'use_welcome_photo':photo,'revision':(old or {}).get('revision',0)+1,
        'run':None,'last_batch':0,'sent':(old or {}).get('sent',0),'failed':(old or {}).get('failed',0),'skipped':(old or {}).get('skipped',0),
        'queued':(old or {}).get('queued',0),'created':(old or {}).get('created',now()),'last_run':(old or {}).get('last_run',0),'last_error':''}
    mode=d.get('text_mode',(old or {}).get('text_mode','plain'));ents=(old or {}).get('text_entities',[])
    if mode=='entities':require(old and c['text']==old['text'],'Use /setcampaign ID to update captured formatting or choose Plain/Markdown.')
    formatted_template(c['text'],mode,ents);c.update(text_mode=mode,text_entities=ents if mode=='entities' else [])
    c['next_at']=random_due(s['settings'],c) if trigger=='random' else now()
    s['campaigns'][cid]=c;check_data_capacity(s);audit(s,uid,'campaign.save',cid)
    return {'id':cid,'message':'Campaign saved. Enable the master switch and external scheduler to deliver to eligible bot users.'}

def promo_wait(s,u):
    st=s['settings'];opened,next_open,day=delivery_window(st)
    if not opened:return next_open
    if u.get('promo_day')==day and u.get('promo_count',0)>=st['campaign_daily_cap']:
        dt=datetime.fromtimestamp(now(),ZoneInfo(st['campaign_timezone']))+timedelta(days=1)
        return int(dt.replace(hour=st['delivery_start_hour'],minute=0,second=0,microsecond=0).timestamp())
    return max(now(),u.get('promo_last_sent',0)+st['campaign_gap_hours']*3600)

def promo_valid(s,v):
    c=s['campaigns'].get(v.get('campaign_id'));u=s['users'].get(v['chat'])
    if not c or not c['enabled'] or not s['settings']['campaigns_enabled'] or not u or not subscriber(u) or v.get('cancelled'):return False
    if v.get('revision')!=c['revision'] or v['t']+86400<=now():return False
    if c['trigger']!='random':
        fp,_=event_for(s,c,u,v.get('fingerprint'))
        if not fp or digest(fp)[:24]!=v.get('fingerprint'):return False
    return True

def engagement_tick(s):
    st=s['settings'];s['system']['last_engagement_tick']=now()
    if not st['campaigns_enabled'] or not delivery_window(st)[0]:return {'queued':0,'scanned':0,'paused':True}
    queued=scanned=0
    ready=[c for c in s['campaigns'].values() if c['enabled'] and not (c['trigger']=='once' and c.get('completed')) and (c.get('run') or c['next_at']<=now())]
    ready.sort(key=lambda c:(c.get('last_batch',0),{'once':0,'expiry':0,'inactive':1,'random':2}[c['trigger']],c['id']))
    for c in ready[:3]:
        if c.get('run') and c['run']['started']+86400<=now():cancel_promos(s,cid=c['id']);c['run']=None
        if not c.get('run'):c['run']={'id':new_id(),'started':now(),'cursor':'','queued':0}
        run=c['run'];c['last_batch']=now()
        users=sorted(k for k in s['users'] if k>run['cursor'])
        for uid in users[:100]:
            if queued>=25 or sum(v.get('kind')=='engagement' for v in s['outbox'].values())>=100 or len(s['outbox'])>=1900:break
            run['cursor']=uid;scanned+=1;u=s['users'][uid]
            if not subscriber(u) or u.get('promo_pending') or promo_wait(s,u)>now():continue
            fp,extra=event_for(s,c,u)
            if not fp:continue
            mark=digest(fp)[:24]
            if c['trigger']!='random' and event_seen(u,c,fp):continue
            text=md(render_marketing(c['text'],u,st,extra))+'\n\n'+md('Daily bot update. To stop delivery, block this bot in Telegram.')
            rows=link_rows(c['links'])+[[btn('My APIs','apis'),btn('Free trial','trial','success')],[btn('Help','help'),btn('Home','home')]]
            key=enqueue(s,uid,text,rows,kind='engagement')
            s['outbox'][key].update(campaign_id=c['id'],revision=c['revision'],fingerprint=mark,
                photo=st['welcome_photo'] if c['use_welcome_photo'] else '',event_target=fp.split(':')[1] if c['trigger']=='expiry' else '')
            if c.get('text_mode','plain')!='plain':attach_rich(s,key,c['text'],c['text_mode'],c.get('text_entities',[]),u,extra,footer='\n\nDaily bot update. To stop delivery, block this bot in Telegram.')
            u['promo_pending']=key;run['queued']+=1;c['queued']+=1;queued+=1
        if not users or run['cursor']>=users[-1]:
            c['last_run']=now();c['run']=None
            if c['trigger']=='once':c['completed']=True
            c['next_at']=random_due(st,c) if c['trigger']=='random' else now()+3600
    return {'queued':queued,'scanned':scanned,'paused':False}

def engagement_state(s,uid):
    st=s['settings'];out={'updates_on':s['users'][uid].get('updates_on',False),'timezone':st['campaign_timezone'],
        'start_hour':st['delivery_start_hour'],'end_hour':st['delivery_end_hour'],'daily_cap':st['campaign_daily_cap'],'gap_hours':st['campaign_gap_hours']}
    if is_admin(uid,s):
        out.update(config={k:copy.deepcopy(st[k]) for k in ENGAGEMENT_KEYS|{'welcome_photo','welcome_video'}},campaigns=list(s['campaigns'].values()),
            subscribers=sum(subscriber(u) for u in s['users'].values()),active_7d=sum(str(u.get('id','')).isdigit() and last_activity(u)>now()-7*86400 for u in s['users'].values()),
            queued=sum(v.get('kind')=='engagement' for v in s['outbox'].values()),last_tick=s['system'].get('last_engagement_tick',0),
            preview_targets=[{'id':k,'name':u['name']} for k,u in s['users'].items() if k.isdigit() and is_admin(k,s) and u.get('telegram_started') and not u.get('blocked')])
    return out

@app.post('/manage/engagement/preferences')
@protected()
def engagement_preferences_route(uid):return jsonify(user_tx(uid,lambda s:updates_preference(s,uid,body().get('enabled'))))

@app.post('/manage/engagement/settings')
@protected(admin=True,elevated=True)
def engagement_settings_route(uid):
    d=body();return jsonify(user_tx(uid,lambda s:engagement_settings(s,uid,d),elevated=True))

@app.post('/manage/campaigns')
@protected(admin=True,elevated=True)
def campaign_save_route(uid):
    d=body();return jsonify(user_tx(uid,lambda s:save_campaign(s,uid,d),elevated=True))

@app.post('/manage/campaigns/<cid>/<action>')
@protected(admin=True,elevated=True)
def campaign_action_route(uid,cid,action):
    body()
    def apply(s):
        c=s['campaigns'].get(cid);require(c is not None,'Campaign not found.',404)
        if action=='delete':
            cancel_promos(s,cid=cid);del s['campaigns'][cid]
            for u in s['users'].values():u.get('campaign_events',{}).pop(cid,None)
        elif action=='toggle':
            c['enabled']=not c['enabled']
            if not c['enabled']:cancel_promos(s,cid=cid);c['run']=None
        elif action=='run':
            require(c['enabled'] and s['settings']['campaigns_enabled'],'Enable this campaign and the master switch first.',409)
            require(not (c['trigger']=='once' and c.get('completed')),'One-time scan completed. Create a new campaign to schedule another broadcast.',409)
            require(not c.get('run'),'This campaign already has a running scan.',409)
            require(c.get('last_manual',0)+300<=now(),'Wait 5 minutes before requesting another run.',429)
            c['next_at']=now();c['last_manual']=now()
        else:raise Problem('Unknown campaign action.',404)
        audit(s,uid,'campaign.'+action,cid)
        return {'message':'Campaign updated. Queued runs still respect bot-start eligibility, exclusions, delivery hours and frequency limits.'}
    return jsonify(user_tx(uid,apply,elevated=True))

@app.post('/manage/engagement/preview')
@protected(admin=True,elevated=True)
def engagement_preview_route(uid):
    d=body();target=str(d.get('target',''));cid=str(d.get('campaign_id',''))
    def preview(s):
        user=actor(s,target,admin=True);require(target.isdigit() and user.get('telegram_started'),'Choose a registered Telegram admin who has opened /start.',403)
        me=s['users'][uid];require(me.get('last_promo_preview',0)+30<=now(),'Wait 30 seconds between previews.',429)
        me['last_promo_preview']=now()
        if not cid:welcome_enqueue(s,target,preview=True)
        else:
            c=s['campaigns'].get(cid);require(c is not None,'Campaign not found.',404)
            extra={'api_name':'Demo API','expires':'Example expiry','days_left':'2','status':'expiring'}
            text='*Campaign preview*\n\n'+md(render_marketing(c['text'],user,s['settings'],extra))
            key=enqueue(s,target,text,link_rows(c['links']),kind='photo' if c['use_welcome_photo'] and s['settings']['welcome_photo'] else 'message')
            if c['use_welcome_photo']:s['outbox'][key]['photo']=s['settings']['welcome_photo']
            if c.get('text_mode','plain')!='plain':attach_rich(s,key,c['text'],c['text_mode'],c.get('text_entities',[]),user,extra,header='Campaign preview\n\n')
        audit(s,uid,'engagement.preview',target)
        return {'message':'Admin preview queued for the selected private Telegram chat.' if not DEMO else 'Demo preview queued only; no Telegram message is sent in demo mode.'}
    result=user_tx(uid,preview,elevated=True);drain(2);return jsonify(result)


# v4.7: verified onboarding, two-sided referrals, operational telemetry and rich text.
OPS_KEYS={'force_join_channels','log_channel','heartbeat_minutes','daily_report_hour','quota_warn_percent','button_icons','supplied_emoji_enabled'}

# v4.15.1: bounded, redacted security alerts; never send Telegram from the error path.
_SECURITY_LOCK=threading.RLock()
_SECURITY_HTTP={}
_SECURITY_HTTP_BUDGET={'minute':-1,'count':0}
_SECURITY_LABELS={
    'panel_denied':'WARNING: non-admin/blocked panel attempt',
    'panel_code':'Admin panel code issued (not yet a login)',
    'login_success':'Successful Telegram admin login',
    'firebase_success':'Successful Firebase admin login',
    'login_denied':'WARNING: web login rejected',
    'admin_denied':'WARNING: admin access/security check rejected',
    'api_abuse':'WARNING: repeated invalid API authentication',
    'rate_limit':'WARNING: request rate limit reached',
    'bot_flood':'WARNING: Telegram flood limit reached',
    'operator_denied':'WARNING: webhook/scheduler authentication rejected',
    'request_guard':'WARNING: request size/traffic guard rejected',
    'service_failure':'WARNING: application request failed',
}

def security_emit(s,entry,count):
    sy=s['system'];minute=now()//60
    if sy.get('security_minute')!=minute:sy.update(security_minute=minute,security_count=0)
    if sy.get('security_count',0)>=10:
        sy['security_suppressed']=min(10**9,sy.get('security_suppressed',0)+count);return False
    sy['security_count']+=1
    audit(s,entry['actor'],'security.'+entry['event'],entry['scope']+'; sampled events: '+str(count))
    return True

def security_notice(s,event,uid,scope,count=1):
    if event not in _SECURITY_LABELS:return
    uid=str(uid);scope=str(scope)
    if not re.fullmatch(r'(?:[0-9]{1,20}|fb:[A-Za-z0-9_-]{1,128}|visitor:[0-9a-f]{16})',uid):uid='unidentified'
    if scope not in ('telegram','panel','login','firebase','api','admin','operator','request'):scope='request'
    stamp=now();cache=s['system'].setdefault('security_events',{})
    for k,v in list(cache.items()):
        if v.get('last',0)+3600<stamp:cache.pop(k,None)
    key=digest(event+'|'+uid+'|'+scope)
    if key not in cache:
        if len(cache)>=256:
            s['system']['security_suppressed']=min(10**9,s['system'].get('security_suppressed',0)+count);return
        cache[key]={'event':event,'actor':uid,'scope':scope,'until':0,'pending':0,'last':stamp}
    entry=cache[key];entry['last']=stamp;entry['pending']=min(10**9,entry['pending']+count)
    if entry['until']<=stamp:
        if security_emit(s,entry,entry['pending']):entry['pending']=0
        entry['until']=stamp+300

def security_summaries(s):
    stamp=now();cache=s['system'].get('security_events',{})
    for key,entry in list(cache.items()):
        if entry.get('pending',0) and entry.get('until',0)<=stamp:
            if security_emit(s,entry,entry['pending']):entry['pending']=0
            entry['until']=stamp+300
        if entry.get('last',0)+3600<stamp:cache.pop(key,None)

def security_http(status,code=''):
    # Only rejected/error requests enter this path. Normal customer calls incur no extra DB transaction.
    if DEMO or store is None or code=='STEP_UP_REQUIRED':return
    endpoint=request.endpoint or '';path=request.path
    if status==429:event,scope='rate_limit','request'
    elif code in ('GUARD_UNAVAILABLE','GUARD_CAPACITY','URL_TOO_LONG','HEADERS_TOO_LARGE','BODY_TOO_LARGE') or status in (413,414,431):event,scope='request_guard','request'
    elif endpoint in ('login_route','firebase_login_route') and status in (400,401,403):event,scope='login_denied','login'
    elif path in ('/telegram/webhook','/tasks/tick','/ops/webhook') and status in (401,403):event,scope='operator_denied','operator'
    elif (path.startswith('/manage/') and status in (401,403)) or path.startswith('/manage/security/') and status==400:event,scope='admin_denied','admin'
    elif endpoint=='invoke' and status in (401,403):event,scope='api_abuse','api'
    elif status>=500:event,scope='service_failure','request'
    else:return
    try:
        uid=getattr(g,'security_actor','') or 'visitor:'+hmac.new(str(cfg('SECRET_KEY')).encode(),client_address().encode(),hashlib.sha256).hexdigest()[:16]
        stamp=now();key=(event,uid,scope)
        with _SECURITY_LOCK:
            if _SECURITY_HTTP_BUDGET['minute']!=stamp//60:_SECURITY_HTTP_BUDGET.update(minute=stamp//60,count=0)
            for old,v in list(_SECURITY_HTTP.items()):
                if v['last']+300<stamp:_SECURITY_HTTP.pop(old,None)
            if key not in _SECURITY_HTTP:
                if len(_SECURITY_HTTP)>=256:return
                _SECURITY_HTTP[key]={'last':stamp,'until':0,'count':0}
            bucket=_SECURITY_HTTP[key];bucket['last']=stamp;bucket['count']=min(10**9,bucket['count']+1)
            if event=='api_abuse' and bucket['count']<5:return
            if bucket['until']>stamp or _SECURITY_HTTP_BUDGET['count']>=10:return
            count=bucket['count'];bucket.update(until=stamp+60,count=0);_SECURITY_HTTP_BUDGET['count']+=1
        store.tx(lambda state:security_notice(state,event,uid,scope,count))
    except Exception:
        # Never replace an authentication rejection with success, or disclose the exception.
        LOG.warning('Security telemetry unavailable; original response retained')

def soft_message(s,chat,text,rows=None,kind='message'):
    if re.fullmatch(r'-?[0-9]{1,20}',str(chat)) and len(s['outbox'])<1900:return enqueue(s,chat,text,rows,kind=kind)
    s['system']['notifications_skipped']=s['system'].get('notifications_skipped',0)+1

def day_counter(target,key,amount=1,keep=30):
    buckets=target.setdefault('daily_stats',{});day=utc_day()
    buckets.setdefault(day,{})[key]=buckets.get(day,{}).get(key,0)+amount
    for old in sorted(buckets)[:-keep]:del buckets[old]

def ops_log(s,event,uid='',detail='',body=None):
    st=s['settings'];sy=s['system'];dest=st.get('log_channel','')
    if not dest or sy.get('log_verified')!=dest or sy.get('log_disabled'):return
    if sy.get('log_minute')!=now()//60:sy.update(log_minute=now()//60,log_count=0)
    if sy.get('log_count',0)>=30 or len(s['outbox'])>=1900:
        sy['log_dropped']=sy.get('log_dropped',0)+1;return
    sy['log_count']=sy.get('log_count',0)+1
    # Event/detail are generated by code; never forward request bodies, URLs, keys or raw exceptions.
    marker='🚨' if any(x in event.lower() for x in ('error','failed','warning','denied','rejected','removed')) else '💙' if 'heartbeat' in event.lower() else '✅'
    return soft_message(s,dest,body if body is not None else '*'+(marker+' ' if focused_ui(s) else '')+'SR DARK · '+md(event)+'*\n'+md('Actor: '+str(uid))+'\n'+md(str(detail)[:180]),kind='opslog')

def ops_audit(s,uid,event,detail=""):
    if event in ('web.login','firebase.login'):
        security_notice(s,'login_success' if event=='web.login' else 'firebase_success',uid,'login' if event=='web.login' else 'firebase');return
    if event.startswith('security.') and event[9:] in _SECURITY_LABELS:
        ops_log(s,_SECURITY_LABELS[event[9:]],uid,detail);return
    important=('user.join','user.activate','user.update','referral.','api.','upstream.failed','backup.','bot.error','forcejoin.','operations.','redeem.','wallet.credit','catalog.update')
    if event.startswith(important):
        safe_detail=str(detail)[:120] if event.startswith(("api.","bot.error","backup.","upstream.failed")) else s["users"].get(str(uid),{}).get("name","")
        ops_log(s,event,uid,safe_detail)

def admin_event(s,uid,event,detail=''):
    labels={'user.join':'New account','user.activate':'Account activated','api.create':'API created / purchased',
        'api.starter.create':'Free starter claimed','api.upgrade':'Starter upgraded','api.key.customize':'Key customized','api.trial.create':'Trial created','api.renew':'API renewed','api.edit':'API settings changed','api.toggle':'API enabled/paused',
        'api.delete':'API deleted','api.rotate':'API key rotated','redeem.claim':'Redeem claimed','redeem.create':'Redeem code created',
        'redeem.revoke':'Redeem code revoked','wallet.credit':'Owner credit added','catalog.update':'Catalogue changed'}
    if event not in labels:return
    # Event detail is never copied verbatim. Only a validated API ID can be attached.
    aid=str(detail) if re.fullmatch(r'api_[0-9a-f]{16}',str(detail)) else ''
    a=s['apis'].get(aid,{})
    record={'id':new_id('notice_'),'t':now(),'event':event,'label':labels[event],'actor':str(uid),'api_id':aid}
    if a:
        record.update(owner=a['owner'],daily=a['daily'],rpm=a['rpm'],expires=a['expires'])
        if event in ('api.create','api.renew'):record.update(coins_charged=0 if is_admin(uid,s) else a.get('price',0),currency=a.get('billing_currency','coins'))
    notices=s.setdefault('admin_notifications',{});notices[record['id']]=record
    while len(notices)>300:del notices[next(iter(notices))]
    if not s['settings'].get('admin_event_notifications'):return
    # Per-minute bounded alerts; the web notification list still records overflow events.
    sy=s['system']
    if sy.get('admin_notice_minute')!=now()//60:sy.update(admin_notice_minute=now()//60,admin_notice_count=0)
    if sy.get('admin_notice_count',0)>=20 or len(s['outbox'])>=1900:
        sy['admin_notice_dropped']=sy.get('admin_notice_dropped',0)+1;return
    sy['admin_notice_count']=sy.get('admin_notice_count',0)+1
    text='*💙 Admin notification*\n'+md(labels[event]+'\nAccount: '+str(uid)+(('\nAPI: '+aid) if aid else ''))
    if 'coins_charged' in record:text+='\n'+md(f"Charged: {record['coins_charged']} {record['currency']}")
    recipients=set(SUPER_IDS)|{i for i,u in s['users'].items() if i.isdigit() and u.get('role')=='admin' and not u.get('blocked')}
    for recipient in sorted(recipients):
        if not str(recipient).isdigit():continue
        k=enqueue(s,recipient,text,[[btn('Admin APIs','adminapis'),btn('Admin','admin')]],kind='admin_event')
        s['outbox'][k]['notice_id']=record['id']

def join_revision(s):return digest(json.dumps(s['settings'].get('force_join_channels',[]),sort_keys=True))[:24]
def joined(s,uid):
    if is_admin(uid,s) or not s['settings'].get('force_join_channels'):return True
    proof=s['users'].get(str(uid),{}).get('join_proof',{})
    return proof.get('revision')==join_revision(s) and proof.get('until',0)>now()

def join_menu(s):
    rows=[[btn('Join '+c['title'],url=c['url'])] for c in s['settings']['force_join_channels']]
    return '*💙 Join our community*\n\n'+md('Join ALL channels/groups below, then press Verify all joins. Join requests must be approved first. Membership checks fail closed if the bot cannot verify a channel.'),rows+[[btn('✓ Verify all joins','verifyjoin','success')],[btn('Help','help'),btn('My ID','id')]]

def request_join(s,uid):
    u=actor(s,uid);require(str(uid).isdigit(),'Use your Telegram account for membership verification.')
    require(u.get('last_join_check',0)+15<=now(),'Wait 15 seconds before checking again.',429)
    require(not any(v.get('kind')=='joincheck' and v['chat']==str(uid) for v in s['outbox'].values()),'Verification already queued.')
    if not s['settings']['force_join_channels']:
        return activate(s,uid)
    require(sum(v.get('kind')=='joincheck' for v in s['outbox'].values())<100 and len(s['outbox'])<1900,'Verification busy; retry shortly.',503)
    key=enqueue(s,uid,'',kind='joincheck');s['outbox'][key].update(revision=join_revision(s),index=0,expires=now()+600)
    u['last_join_check']=now();return 'Checking every required channel/group. Keep this chat open; the scheduler finishes queued checks.'

def join_probe(s,v):
    channels=s['settings']['force_join_channels'];i=v.get('index',0)
    if v.get('revision')!=join_revision(s) or i>=len(channels):return {'stale':True}
    bot=s['system'].get('bot_identity',{})
    if not bot.get('id') or bot.get('token_fingerprint')!=digest(cfg('BOT_TOKEN')):
        bot=tg('getMe',{});require(bot.get('is_bot') is True,'Bot identity unavailable.')
    chat=channels[i]['chat_id']
    own=tg('getChatMember',{'chat_id':chat,'user_id':int(bot['id'])})
    require(own.get('status') in ('administrator','creator'),'Bot must be an administrator in every required channel/group.')
    member=tg('getChatMember',{'chat_id':chat,'user_id':int(v['chat'])})
    ok=member.get('status') in ('member','administrator','creator') or (member.get('status')=='restricted' and member.get('is_member') is True)
    return {'joined':ok,'index':i,'title':channels[i]['title']}

def join_finish(s,k,v,result):
    u=s['users'].get(v['chat']);current=s['outbox'].get(k)
    if not current:return
    if not u or u.get('blocked') or result.get('stale') or v['revision']!=join_revision(s):
        s['outbox'].pop(k,None);return
    if not result['joined']:
        u.pop('join_proof',None);s['outbox'].pop(k,None)
        text,rows=join_menu(s);soft_message(s,v['chat'],md('Not joined: '+result['title'])+'\n\n'+text,rows)
        return
    if result['index']+1<len(s['settings']['force_join_channels']):
        current.update(index=result['index']+1,lease=0,next=now()+1,tries=0);return
    s['outbox'].pop(k,None);u['join_proof']={'revision':v['revision'],'until':now()+300}
    activate(s,v['chat']);audit(s,v['chat'],'forcejoin.verified')
    soft_message(s,v['chat'],'*✅ All joins verified*\n'+md('Account activated. Referral rewards, if eligible, were applied once.'),[[btn('Open dashboard','home','success')]])

def settle_referral(s,rid):
    r=s['referrals'][rid]
    require(r['status']=='pending','Referral is not pending.')
    inviter=s['users'].get(r['from']);invitee=s['users'].get(r['to'])
    require(inviter and invitee and not inviter.get('blocked') and not invitee.get('blocked'),'Referral account unavailable.')
    # Membership was verified at qualification; approval does not mint another reward.
    reward=r['reward'];new_reward=r.get('new_user_reward',0)
    wallet_change(s,r['from'],'coins',reward,'Approved referral',rid)
    if new_reward:wallet_change(s,r['to'],'coins',new_reward,'Referred-user welcome reward',rid)
    inviter['refs']=inviter.get('refs',0)+1;r.update(status='approved',paid_at=now())
    day_counter(s['system'],'referrals');day_counter(s['system'],'reward_coins',reward+new_reward)
    soft_message(s,r['from'],'*🎉 Referral qualified*\n'+md(f"{invitee['name']} completed onboarding.\n+{reward} coins · Balance: {inviter['coins']} coins"),[[btn('Share referral','refs','success')]])
    soft_message(s,r['to'],'*💙 Welcome reward*\n'+md(f"Invited by {inviter['name']}.\n+{new_reward} coins · Balance: {invitee['coins']} coins"),[[btn('API catalogue','create'),btn('Invite friends','refs','success')]])
    audit(s,r['from'],'referral.approved',rid)

def referral_requirement(s,uid,source=None):
    currency,price=api_price(s,source)
    if currency!='coins':return f'{price} diamonds · referral coins cannot pay this source'
    reward=s['settings']['referral_reward'];balance=s['users'][uid].get('coins',0)
    return f"{price} coins · {math.ceil(price/reward)} referrals from zero · {math.ceil(max(0,price-balance)/reward)} more with your current balance"

def statistics(s,uid,admin=False):
    if admin:actor(s,uid,admin=True)
    apis=[a for a in s['apis'].values() if admin or a['owner']==str(uid)]
    days=[(datetime.fromtimestamp(now(),timezone.utc)-timedelta(days=i)).date().isoformat() for i in range(6,-1,-1)]
    buckets=s['system'].get('daily_stats',{}) if admin else {}
    if not admin:
        for a in apis:
            for day,b in a.get('daily_stats',{}).items():
                d=buckets.setdefault(day,{})
                for key,n in b.items():d[key]=d.get(key,0)+n
    series=[{'day':d,**{k:buckets.get(d,{}).get(k,0) for k in ('calls','ok','errors','new_users','referrals','reward_coins')}} for d in days]
    result={'scope':'workspace' if admin else 'your current APIs','series':series,'apis':len(apis),
        'active_apis':sum(a['active'] and a['expires']>now() for a in apis),
        'total_calls':sum(a.get('calls',0) for a in apis),'today_used':sum(a.get('used',0) for a in apis if a.get('day')==utc_day()),
        'today_limit':sum(a['daily'] for a in apis if a['active'] and a['expires']>now()),'today':series[-1]}
    if focused_ui(s):
        result['active_apis']=sum(a['active'] and a['expires']>now() and not (a.get('is_trial') and a.get('calls',0)>=a.get('trial_limit',0)) and not (a.get('total_limit') and a.get('calls',0)>=a['total_limit']) for a in apis)
        paid=[a for a in apis if not a.get('is_trial') and a['active'] and a['expires']>now()]
        result['today_used']=sum(a.get('used',0) for a in paid if a.get('day')==utc_day())
        result['today_limit']=sum(a['daily'] for a in paid if a['active'] and a['expires']>now())
        result['trial_used']=sum(a.get('calls',0) for a in apis if a.get('is_trial'))
        result['trial_budget']=sum(a.get('trial_limit',0) for a in apis if a.get('is_trial'))
    if admin:result.update(users=len(s['users']),active_users=sum(u.get('active',False) for u in s['users'].values()),
        new_users_today=sum(utc_date(u['joined'])==utc_day() for u in s['users'].values()),
        queue=len(s['outbox']),last_tick=s['system'].get('last_tick',0),last_backup=s['system'].get('last_backup',0),
        backup_locations=s['system'].get('backup_locations',[]),storage=store.kind)
    return result

def utc_date(t):return datetime.fromtimestamp(t,timezone.utc).date().isoformat()
def stats_message(s,uid,admin=False):
    d=statistics(s,uid,admin);mx=max(1,max(x['calls'] for x in d['series']))
    chart='\n'.join(x['day'][5:]+' '+('▰'*math.ceil(x['calls']/mx*10) if x['calls'] else '·')+' '+str(x['calls']) for x in d['series'])
    text='*📊 '+('Admin statistics' if admin else 'Your API statistics')+'*\n\n'+md(f"APIs: {d['apis']} · Active: {d['active_apis']}\nToday: {d['today']['calls']} calls · {d['today']['errors']} errors\nCurrent APIs total calls: {d['total_calls']}\nDaily quota used: {d['today_used']} / {d['today_limit']}")
    if 'trial_budget' in d:text+='\n'+md(f"Short-demo total use: {d['trial_used']} / {d['trial_budget']} (not a daily quota)")
    if admin:text+='\n'+md(f"Users: {d['users']} · New today: {d['new_users_today']}\nQualified referrals today: {d['today']['referrals']}\nQueue: {d['queue']} · Storage: {d['storage']}\nLast scheduler: {iso(d['last_tick']) if d['last_tick'] else 'not run'}\nLast backup: {iso(d['last_backup']) if d['last_backup'] else 'not run'}")
    if admin and focused_ui(s):text+='\n'+md('Version: '+VERSION+' · Worker: '+('embedded active' if worker_available() else 'foreground / external scheduler')+(('\nLast webhook: DB '+str(_BOT_TIMINGS['database_ms'])+'ms · foreground delivery '+str(_BOT_TIMINGS['delivery_ms'])+'ms') if _BOT_TIMINGS else ''))
    return text+'\n\n*7 days · UTC calls*\n'+code(chart)+'\n'+md('Charts start with v4.7; earlier history is not reconstructed.')

def ops_settings(s,uid,d):
    actor(s,uid,superonly=True);require(isinstance(d,dict) and set(d)<=OPS_KEYS,'Unknown operation setting.')
    change={}
    if 'force_join_channels' in d:
        items=d['force_join_channels'];require(isinstance(items,list) and len(items)<=5,'Use up to five required channels/groups.')
        channels=[];seen=set()
        for c in items:
            require(isinstance(c,dict),'Invalid channel entry.')
            chat=str(c.get('chat_id','')).strip();title=marketing_text(c.get('title',''),'Channel title',40);url=str(c.get('url',''))
            require(re.fullmatch(r'(?:@[A-Za-z][A-Za-z0-9_]{4,31}|-[1-9][0-9]{4,19})',chat),'Use @channel or a negative Telegram chat ID.')
            link=urllib.parse.urlsplit(url)
            require(link.scheme=='https' and link.hostname=='t.me' and not link.username and not link.password and not link.port and re.fullmatch(r'/[A-Za-z0-9_+/-]{3,150}',link.path) and not link.query and not link.fragment,'Use an HTTPS t.me username or invite link.')
            require(chat.lower() not in seen,'Duplicate channel.');seen.add(chat.lower());channels.append({'chat_id':chat,'title':title,'url':url})
        change['force_join_channels']=channels
    if 'supplied_emoji_enabled' in d:
        require(type(d['supplied_emoji_enabled']) is bool,'Supplied emoji toggle must be boolean.');change['supplied_emoji_enabled']=d['supplied_emoji_enabled']
    if 'log_channel' in d:
        dest=str(d['log_channel']).strip();require(not dest or re.fullmatch(r'-[1-9][0-9]{4,19}',dest),'Logs require a private channel/group numeric ID, e.g. -100…')
        change['log_channel']=dest
    for k,lo,hi in [('heartbeat_minutes',5,1440),('daily_report_hour',0,23),('quota_warn_percent',50,95)]:
        if k in d:change[k]=integer(d[k],k,lo,hi)
    if 'button_icons' in d:
        icons=d['button_icons'];require(isinstance(icons,dict) and set(icons)<={'primary','success','danger'},'Use primary/success/danger icon IDs.')
        require(all(isinstance(v,str) and (not v or re.fullmatch(r'[0-9]{1,32}',v)) for v in icons.values()),'Custom emoji IDs must be numeric strings.')
        change['button_icons']={k:v for k,v in icons.items() if v}
    merged={**s['settings'],**change}
    require(not merged['log_channel'] or merged['log_channel'] not in {c['chat_id'] for c in merged['force_join_channels']},'Keep private logs separate from required join channels.')
    if 'force_join_channels' in change:
        for k,v in list(s['outbox'].items()):
            if v.get('kind')=='joincheck':del s['outbox'][k]
    if 'log_channel' in change and change['log_channel']!=s['settings'].get('log_channel'):
        s['system'].update(log_verified='',log_disabled=False)
        for k,v in list(s['outbox'].items()):
            if v.get('kind') in ('opslog','logverify'):del s['outbox'][k]
    if change.get('supplied_emoji_enabled') is True:s['system'].pop('supplied_emoji_disabled_until',None)
    s['settings'].update(change);check_data_capacity(s);audit(s,uid,'operations.settings')
    return {'message':'Saved. Add the bot as admin in every required channel/group. Verify the private logs destination before logs start.'}

def prune_expired_log_checks(s):
    for k,v in list(s['outbox'].items()):
        if v.get('kind')=='logverify' and v.get('expires',0)<=now() and v.get('lease',0)<=now():
            del s['outbox'][k]

def log_check_error(error):
    code=getattr(error,'api_code',0)
    if code==400:return 'Telegram cannot access this chat ID (or the ID is invalid). Add this bot as admin in the intended private group and send /loghere there.'
    if code==403:return 'Telegram denied access. Add/unblock the bot and grant administrator permissions in the private logs destination.'
    if code==429:return 'Telegram rate-limited the check. Wait for the retry time, then verify again; a running worker can retry automatically.'
    if isinstance(error,Problem):return error.message
    return 'Telegram verification temporarily unavailable. Retry, or leave a worker running. No destination was changed.'

def run_requested_log_check(key):
    # Only this job is attempted. Durable leases and Telegram backoff still apply.
    drain(1,12,job_id=key)
    state=store.read();check=state['system'].get('log_check',{})
    if check.get('job_id')==key and check.get('state')=='verified' and check.get('proof_job'):
        drain(1,6,job_id=check['proof_job'])
        state=store.read();check=state['system'].get('log_check',{})
    if check.get('job_id')==key and check.get('state') in ('verified','failed','cancelled'):
        verified=check['state']=='verified' and not state['system'].get('log_disabled') and state['system'].get('log_verified')==check.get('target')==state['settings'].get('log_channel')
        message=check['message']
        if verified:
            message+=' Test message sent to the group.' if check.get('test_sent') else ' Test message is awaiting delivery; check Telegram backoff/worker status.'
        elif check['state']=='verified':message='Permissions were verified, but test delivery failed or the destination changed. Check bot access and verify again.'
        return {'status':'verified' if verified else 'failed','message':message,'test_sent':bool(check.get('test_sent'))}
    job=state['outbox'].get(key)
    if not job:return {'status':'cancelled','message':'Verification expired or settings changed. Verify again.'}
    retry=max(now()+1,job.get('next',0),job.get('lease',0),state['system'].get('telegram_retry_at',0))
    reason=check.get('message') if check.get('job_id')==key and check.get('state')=='waiting' else 'Verification is waiting for Telegram backoff or an active check, not the ordinary message queue.'
    return {'status':'waiting','retry_at':retry,'message':reason+' Next eligible check: '+iso(retry)+'. Retry then or keep the worker running.'}

def queue_log_test(s,uid):
    actor(s,uid,superonly=True);dest=s['settings'].get('log_channel');require(dest,'Set a private logs channel/group first.')
    require(s['system'].get('log_test_at',0)+30<=now(),'Wait 30 seconds before testing logs.',429)
    prune_expired_log_checks(s)
    for existing,job in s['outbox'].items():
        if job.get('kind')=='logverify' and job['chat']==str(uid) and job.get('target')==dest and job.get('lease',0)<=now():
            s['system']['log_test_at']=now()
            return {'message':'Retrying the saved check now.','job_id':existing}
    require(not any(v.get('kind')=='logverify' for v in s['outbox'].values()),'A verification check is already active. Retry after its five-minute timeout.',409)
    k=enqueue(s,uid,'',kind='logverify');s['outbox'][k].update(target=dest,expires=now()+300,priority=-10)
    s['system'].update(log_test_at=now(),log_check={'job_id':k,'target':dest,'state':'checking','t':now(),'message':'Checking Telegram access now.'})
    return {'message':'Checking private logs now. The result follows in this request.','job_id':k}

def log_probe(v):
    chat=tg('getChat',{'chat_id':v['target']});require(chat.get('type') in ('channel','supergroup','group') and not chat.get('username') and not chat.get('active_usernames'),'Use a private admin-only logs channel/group, not a public channel.')
    me=tg('getMe',{});own=tg('getChatMember',{'chat_id':v['target'],'user_id':me['id']})
    require(own.get('status') in ('creator','administrator'),'Bot must be admin in the log destination.')
    require(chat['type']!='channel' or own.get('status')=='creator' or own.get('can_post_messages') is True,'Grant the bot Post Messages permission.')
    return True

def operational_tick(s):
    sy=s['system'];st=s['settings'];sy['last_tick']=now();security_summaries(s)
    if sy.get('backup_id'):queue_backup_deliveries(s,sy['backup_id'])
    for a in s['apis'].values():
        if a['active'] and 0<a['expires']-now()<=86400 and a.get('expiry_notice')!=a['expires']:
            a['expiry_notice']=a['expires'];ops_log(s,'api.expiry.warning',a['owner'],a['id']+' expires within 24h')
    if sy.get('log_verified')!=st.get('log_channel') or not st.get('log_channel') or sy.get('log_disabled'):return
    if sy.get('last_heartbeat',0)+st['heartbeat_minutes']*60<=now():
        sy['last_heartbeat']=now();ops_log(s,'💙 heartbeat','scheduler',f"v{VERSION} tick active · queue {len(s['outbox'])} · users {len(s['users'])} · APIs {len(s['apis'])} · backup {iso(sy['last_backup']) if sy.get('last_backup') else 'not run'}")
    day=utc_day()
    if datetime.fromtimestamp(now(),timezone.utc).hour>=st['daily_report_hour'] and sy.get('daily_report')!=day:
        sy['daily_report']=day
        yesterday=(datetime.fromtimestamp(now(),timezone.utc)-timedelta(days=1)).date().isoformat();b=sy.get('daily_stats',{}).get(yesterday,{})
        summary=f"{yesterday} UTC · new users {b.get('new_users',0)} · calls {b.get('calls',0)} · errors {b.get('errors',0)} · referrals {b.get('referrals',0)} · dropped log events {sy.get('log_dropped',0)}"
        dates=[(datetime.fromtimestamp(now(),timezone.utc)-timedelta(days=i)).date().isoformat() for i in range(7,0,-1)]
        counts=[sy.get('daily_stats',{}).get(d,{}).get('calls',0) for d in dates];maximum=max(1,max(counts))
        diagram='\n'.join(d[5:]+' '+('▰'*math.ceil(n/maximum*10) if n else '·')+' '+str(n) for d,n in zip(dates,counts))
        ops_log(s,'📊 Daily report','scheduler',body='*📊 Daily report*\n'+md(summary)+'\n\n*Last 7 complete days · calls*\n'+code(diagram))

def quota_notice(s,a,reason):
    day='trial' if a.get('is_trial') else utc_day();marks=a.setdefault('warning_marks',{})
    if marks.get('day')!=day:marks.clear();marks['day']=day
    if marks.get(reason):return
    marks[reason]=now();used=a.get('used',0) if a.get('day')==day else 0
    if a.get('is_trial'):used=a['calls']
    usage=f"Trial: {used}/{a['trial_limit']} · budget never resets" if a.get('is_trial') else f"Usage: {used}/{a['daily']} · resets 00:00 UTC"
    msg='*⚠️ API warning*\n'+md(a['name']+' · '+reason+'\n'+usage)
    soft_message(s,a['owner'],msg,[[btn('My APIs','apis')]])
    ops_log(s,'api.warning',a['owner'],a['id']+' · '+reason+f' · {used}/{a["daily"]}')

def guard_notice(s,aid,key,reason):
    a=s['apis'].get(aid)
    if not a or not key or not hmac.compare_digest(a['key_hash'],digest(key)):return
    quota_notice(s,a,{'DAILY_LIMIT':'Daily quota reached','TRIAL_LIMIT':'Trial quota reached'}.get(reason,reason))

def rich_entities(text,entities):
    require(isinstance(entities,list) and len(entities)<=64,'At most 64 text entities allowed.')
    bounds={0};n=0
    for ch in text:n+=text_units(ch);bounds.add(n)
    out=[]
    for e in entities:
        require(isinstance(e,dict),'Invalid text entity.')
        typ=e.get('type')
        if typ not in ('bold','italic','underline','strikethrough','spoiler','code','pre','text_link','custom_emoji'):continue
        o=e.get('offset');l=e.get('length');require(type(o) is int and type(l) is int and l>0 and o in bounds and o+l in bounds,'Invalid UTF-16 entity boundary.')
        item={'type':typ,'offset':o,'length':l}
        if typ=='text_link':
            url=e.get('url','');p=urllib.parse.urlsplit(url)
            require(isinstance(url,str) and len(url)<=500 and p.scheme=='https' and p.hostname and not p.username and not p.password and not any(ord(c)<=32 for c in url),'Formatted links must use HTTPS without credentials.')
            item['url']=url
        if typ=='custom_emoji':
            value=str(e.get('custom_emoji_id',''));require(re.fullmatch(r'[0-9]{1,32}',value),'Invalid custom emoji ID.');item['custom_emoji_id']=value
        if typ=='pre' and e.get('language'):item['language']=str(e['language'])[:24]
        out.append(item)
    for i,e in enumerate(out):
        a,b=e['offset'],e['offset']+e['length']
        for f in out[i+1:]:
            c,d=f['offset'],f['offset']+f['length']
            require(not (a<c<b<d or c<a<d<b),'Text entities cannot cross each other.')
            require(not (max(a,c)<min(b,d) and (e['type'] in ('code','pre') or f['type'] in ('code','pre'))),'Code/pre cannot overlap other formatting.')
    return sorted(out,key=lambda e:(e['offset'],-e['length']))

def parse_markdown(source,max_units=1800):
    # Deliberately bounded subset; no HTML, raw mentions, code execution or remote fetches.
    require(isinstance(source,str) and text_units(source)<=max_units,'Markdown too long.')
    text=[];entities=[];pos=0;units=0
    def emit(t):
        nonlocal units
        text.append(t);units+=text_units(t)
    def parse(stop='',depth=0):
        nonlocal pos
        require(depth<=6,'Markdown nesting exceeds six levels.')
        while pos<len(source):
            if stop and source.startswith(stop,pos):pos+=len(stop);return
            if source[pos]=='\\':
                require(pos+1<len(source),'Trailing Markdown escape.');emit(source[pos+1]);pos+=2;continue
            if source.startswith('```',pos) or source[pos]=='`':
                token='```' if source.startswith('```',pos) else '`';pos+=len(token);end=source.find(token,pos)
                require(end>=0,'Unclosed code formatting.');start=units;emit(source[pos:end]);pos=end+len(token)
                if units>start:entities.append({'type':'pre' if token=='```' else 'code','offset':start,'length':units-start})
                continue
            if source[pos]=='[':
                mid=source.find('](',pos+1);end=source.find(')',mid+2) if mid>=0 else -1
                require(mid>=0 and end>=0,'Use [label](https://example.com) for links.')
                label=source[pos+1:mid];url=source[mid+2:end];require(bool(label),'Link label required.')
                start=units;emit(label);entities.append({'type':'text_link','offset':start,'length':units-start,'url':url});pos=end+1;continue
            token=next((t for t in ('__','||','*','_','~') if source.startswith(t,pos)),None)
            if token:
                start=units;pos+=len(token);parse(token,depth+1)
                require(units>start,'Empty formatting is not allowed.')
                entities.append({'type':{'*':'bold','_':'italic','__':'underline','~':'strikethrough','||':'spoiler'}[token],'offset':start,'length':units-start});continue
            emit(source[pos]);pos+=1
        require(not stop,'Unclosed Markdown formatting.')
    parse();value=''.join(text);return value,rich_entities(value,entities)

def formatted_template(text,mode='plain',entities=None):
    require(mode in ('plain','markdown','entities'),'Unknown message format.')
    if mode=='markdown':return parse_markdown(text)
    return text,rich_entities(text,entities or []) if mode=='entities' else []

def render_rich(text,mode,entities,u,st,extra=None):
    raw,ents=formatted_template(text,mode,entities)
    values={'name':u['name'],'coins':str(u.get('coins',0)),'diamonds':str(u.get('diamonds',0)),
            'referral_reward':str(st['referral_reward']),'api_price':str(st['default_api_price']),**(extra or {})}
    parts=[];mapping={0:0};old=new=0;cursor=0
    for match in re.finditer(r'\{([a-z_]+)\}',raw):
        if match[1] not in values:continue
        for ch in raw[cursor:match.start()]:
            parts.append(ch);old+=text_units(ch);new+=text_units(ch);mapping[old]=new
        start=old;old+=text_units(match[0]);value=str(values[match[1]])
        for e in ents:require(not (start<e['offset']<old or start<e['offset']+e['length']<old),'Formatting must cover the entire placeholder.')
        parts.append(value);new+=text_units(value);mapping[old]=new;cursor=match.end()
    for ch in raw[cursor:]:parts.append(ch);old+=text_units(ch);new+=text_units(ch);mapping[old]=new
    result=clip_text(''.join(parts),700);limit=text_units(result);out=[]
    for e in ents:
        a=mapping[e['offset']];b=min(limit,mapping[e['offset']+e['length']])
        if b>a:out.append({**e,'offset':a,'length':b-a})
    return result,out

def attach_rich(s,key,text,mode,entities,u,extra=None,header='',footer=''):
    body,ents=render_rich(text,mode,entities,u,s['settings'],extra)
    shift=text_units(header);message=header+body+footer
    s['outbox'][key].update(text=message,plain_text=True,entities=[{**e,'offset':e['offset']+shift} for e in ents])

def capture_message(s,uid,message,flow):
    actor(s,uid,admin=True);require(flow.get('t',0)+600>now(),'Message capture expired.')
    raw=message.get('text') or message.get('caption');require(isinstance(raw,str),'Send a formatted text message or photo caption.')
    # Preserve Telegram UTF-16 offsets exactly; do not trim captured content.
    require(0<text_units(raw)<=700,'Formatted message must be 1–700 text units.')
    ents=rich_entities(raw,(message.get('entities') if message.get('text') else message.get('caption_entities')) or [])
    if flow.get('step')=='welcome_md':raw=marketing_text(raw,'Markdown');parse_markdown(raw);mode='markdown';ents=[]
    else:mode='entities'
    if flow.get('campaign'):
        c=s['campaigns'].get(flow['campaign']);require(c,'Campaign no longer exists.')
        c.update(text=raw,text_mode=mode,text_entities=ents,revision=c['revision']+1,run=None);cancel_promos(s,cid=c['id'])
    else:s['settings'].update(welcome_caption=raw,welcome_mode=mode,welcome_entities=ents,welcome_dashboard=False)
    s['users'][uid]['flow']={};check_data_capacity(s);audit(s,uid,'message.capture')
    return 'Formatted message saved. Use the admin preview before enabling delivery. Custom emoji playback depends on Telegram bot eligibility.'

@app.post('/manage/operations')
@protected(superonly=True,elevated=True)
def operations_route(uid):return jsonify(user_tx(uid,lambda s:ops_settings(s,uid,body()),elevated=True))

@app.post('/manage/operations/testlogs')
@protected(superonly=True,elevated=True)
def operations_logtest_route(uid):
    r=user_tx(uid,lambda s:queue_log_test(s,uid),elevated=True)
    return jsonify(run_requested_log_check(r['job_id']))


# Compact customer screens; legacy business records and admin tools are preserved.
def simple_ui(s):return bool(s['settings'].get('simple_customer_ui'))

SIMPLE_COMMANDS=[('start','Home'),('create','API store'),('apis','My APIs'),('buy','Buy credits'),('wallet','My balance'),('referral','Invite and earn'),('help','Help')]

def simple_home(s,uid):
    u=s['users'][str(uid)]
    active=sum(a['owner']==str(uid) and a['active'] and a['expires']>now() and not (a.get('is_trial') and a.get('calls',0)>=a.get('trial_limit',0)) and not (a.get('total_limit') and a.get('calls',0)>=a['total_limit']) for a in s['apis'].values())
    display_name=' '.join(str(u.get('name') or 'Member').split()) or 'Member'
    status='On hold' if u.get('wallet_hold') else 'Active' if u.get('active') else 'Activation needed'
    text=('*💙 SR DARK*\n_API Dashboard_\n'
          +'━━━━━━━━━━━━━━━━━━\n'
          +'👤 *Name:* '+md(display_name)+'\n'
          +'🆔 *ID:* '+code(str(uid))+'\n\n'
          +'💰 *Balance:* '+md(format(u['coins'],',')+' credits')+'\n'
          +'🔑 *Active APIs:* '+md(str(active))+'\n'
          +'✅ *Status:* '+md(status)+'\n'
          +'━━━━━━━━━━━━━━━━━━\n'
          +'_Choose an option below_')
    rows=[[btn('API Store','create'),btn('My APIs','apis')],[btn('Buy Credits','buy','success'),btn('Wallet','wallet')],[btn('Invite & Earn','refs'),btn('Help','help')]]
    if not u.get('active'):rows.insert(0,[btn('Activate','activate','success')])
    if is_admin(uid,s):rows.append([btn('Admin','admin'),btn('Admin Panel','panel')])
    return text,rows

def credit_signature(pack):return digest(json.dumps({k:pack[k] for k in ('id','amount','stars','currency')},sort_keys=True))[:12]

def simple_credits(s,uid,page=0):
    packs=[p for p in s['settings']['purchase_packs'] if p['enabled'] and p['currency']=='coins']
    pages=max(1,(len(packs)+5)//6);page=max(0,min(page,pages-1));part=packs[page*6:(page+1)*6]
    text='*Buy Credits*\n\n'+md('Balance: '+str(s['users'][str(uid)]['coins'])+' credits (coins)\nChoose a pack. Pay securely with Telegram Stars.\nCredits are added after successful payment.')
    rows=[]
    for p in part:
        text+='\n\n'+md(str(p['amount'])+' credits  •  '+str(p['stars'])+' Stars')
        rows.append([btn('Buy '+str(p['amount'])+' credits · '+str(p['stars'])+' Stars','creditbuy:'+p['id']+':'+credit_signature(p),'success')])
    if not packs:text+='\n\n'+md('No credit packs available yet.')
    nav=[]
    if page:nav.append(btn('Back','creditpage:'+str(page-1)))
    if page+1<pages:nav.append(btn('More','creditpage:'+str(page+1)))
    if nav:rows.append(nav)
    rows.append([btn('Terms','terms'),btn('Home','home')]);return text,rows

def simple_payment_help(s):
    name=s['settings'].get('support_username','')
    text='*Payment issue*\n'+md('For a payment or refund issue, contact '+('@'+name if name else 'the configured owner')+'. Share only your order ID; never share API keys, passwords or OTPs.')
    rows=[]
    if name:rows.append([btn('Payment contact',url='https://t.me/'+name)])
    elif SUPER_IDS:rows.append([btn('Payment contact',url='tg://user?id='+sorted(SUPER_IDS)[0])])
    rows.append([btn('Wallet','wallet'),btn('Home','home')]);return text,rows

def simple_customer_action(s,uid,action,raw,cb):
    if not simple_ui(s):return None
    u=s['users'][uid]
    if action in ('buy','ownerbuy','contactbuy') or action.startswith(('ownerbuy:','ownerpick:','ownerpack:','buy:')):
        u['flow']={};return simple_credits(s,uid)
    if action.startswith('creditpage:'):
        value=action.split(':')[1];require(value.isdigit() and len(value)<=6,'Invalid page.');u['flow']={};return simple_credits(s,uid,int(value))
    if action.startswith('creditbuy:'):
        _,pid,quote=action.split(':',2)
        p=next((p for p in s['settings']['purchase_packs'] if p['id']==pid and p['enabled'] and p['currency']=='coins'),None)
        require(p and hmac.compare_digest(credit_signature(p),quote),'Pack changed. Open Buy Credits again.',409)
        result=new_order(s,uid,pid);u['flow']={}
        return md('Invoice ready for '+str(p['amount'])+' credits. Pay '+str(p['stars'])+' Stars in Telegram. Your balance changes after successful payment.'),[[btn('Wallet','wallet'),btn('Home','home')]]
    if action=='wallet':
        u['flow']={};text='*Wallet*\n\n'+md('Balance: '+str(u['coins'])+' credits (coins)')
        if u.get('diamonds'):text+='\n'+md('Diamonds: '+str(u['diamonds']))
        if u.get('wallet_hold'):text+='\n'+md('Wallet on hold. Use /paysupport for a payment issue.')
        rows=[[btn('Buy Credits','buy','success'),btn('Redeem code','redeem')],[btn('My Usage','mystats'),btn('Home','home')]]
        if u.get('diamonds') and s['settings']['diamond_coin_rate']>0:rows.insert(1,[btn('Convert diamonds','convert')])
        return text,rows
    if action in ('paysupport','contacthelp'):
        u['flow']={};return simple_payment_help(s)
    if action.startswith(('support','ownerrequest')) or u.get('flow',{}).get('step') in ('support_chat','support_reply','owner_quote'):
        u['flow']={};return md('General support chat is no longer available. Use the menu below.'),[[btn('API Store','create'),btn('Buy Credits','buy')],[btn('Home','home')]]
    if not is_admin(uid,s):
        f=u.get('flow',{})
        if f.get('draft',{}).get('mode') in ('static','proxy','validation') and action in ('','confirmcreate'):
            u['flow']={};return md('Custom API creation is no longer available.'),[[btn('API Store','create')]]
        if action in ('customcreate','newstatic','newproxy'):
            u['flow']={};return md('Choose an API from the store. Custom API creation is not available.'),[[btn('API Store','create'),btn('Home','home')]]
        if action.startswith('edit:'):
            a=owned(s,uid,action.split(':',1)[1])
            if a['mode']!='catalog':
                u['flow']={};return md('Custom source editing is no longer available. Your existing API and key remain unchanged.'),[[btn('My APIs','apis'),btn('Home','home')]]
    return None


# Role-scoped help and Telegram command menus (no network inside transactions).
USER_COMMANDS=[('contact','Ask the owner about buying/support'),('freeapi','One free 10-day starter API'),('redeem','Redeem a gift code'),('start','Open your dashboard'),('help','User help'),('trial','One-time API trial'),('buyapi','Choose API type and buy with coins'),('create','Open the API catalogue'),
    ('apis','Manage your APIs'),('stats','Your API statistics'),('referral','Invite and earn coins'),
    ('wallet','Your wallet'),('buy','Available Stars packs'),('verify','Verify required joins'),
    ('developer','API documentation'),('terms','Purchase terms'),('paysupport','Payment support'),
    ('demo','Get your one-time trial API'),('cancel','Cancel a wizard'),('id','Your Telegram ID')]
ADMIN_COMMANDS=[('commands','All controls as buttons'),('delivery','Private credential delivery format'),('confirm','Unlock a sensitive browser session'),('adminapis','All APIs: view and edit limits'),('broadcast','Compose and confirm broadcast'),('admin','Admin control centre'),('adminhelp','Admin-only help'),('adminstats','Workspace statistics'),
    ('panel','Admin CRUD panel'),('setwelcome','Select welcome photo'),('setvideo','Select welcome video'),('dashboard','Use dynamic welcome dashboard'),('sources','Source IDs'),('addsource','Publish a customer source'),('addplan','Add source pricing plan'),
    ('removesticker','Remove welcome sticker'),('botstyle','Bot appearance'),('setmessage','Capture formatted welcome'),
    ('setwelcomemd','Set Markdown welcome'),('setcampaign','Capture campaign text'),('confirm','Confirm protected changes'),('cancel','Cancel admin wizard')]
OWNER_COMMANDS=[('support','Customer support inbox'),('approvals','Review pending sensitive actions'),('forcejoin','Add required group/channel with picker'),('loghere','Connect private logs group: send there'),('addcredit','Credit coins with confirmation'),('createredeem','Create limited-use redeem code'),('revokeredeem','Revoke a redeem code'),('logs','Verify private logs destination'),('operations','Force-join and private logs'),('setbuttonemoji','Capture button custom emoji'),('backup','Request encrypted backup')]

def commands_for(s,uid):
    admin=is_admin(uid,s) and not s['users'].get(str(uid),{}).get('blocked')
    pairs=(USER_COMMANDS if s['settings'].get('modern_controls') else [])+ADMIN_COMMANDS+(OWNER_COMMANDS if role(uid,s)=='superadmin' else []) if admin else USER_COMMANDS
    if simple_ui(s):pairs=SIMPLE_COMMANDS+(ADMIN_COMMANDS+[(c,d) for c,d in OWNER_COMMANDS if c!='support'] if admin else [])
    if not focused_ui(s) and not admin:pairs=pairs+[('commands','All controls as buttons'),('delivery','Private credential delivery format')]
    return [{'command':name,'description':'Buy credits with Stars' if name=='buy' and simple_ui(s) else 'Prices and owner inquiry' if name=='buy' and focused_ui(s) else description} for name,description in dict(pairs).items()]

def queue_commands(s,uid,force=False):
    uid=str(uid);u=s['users'].get(uid)
    if not uid.isdigit() or not u or not u.get('telegram_started'):return
    commands=commands_for(s,uid);mark=digest(json.dumps(commands,sort_keys=True))
    if not force and u.get('command_menu_hash')==mark:return
    # Normal users inherit the public user-only list. Only replace a prior scoped menu.
    if not force and not simple_ui(s) and not is_admin(uid,s) and not u.get('command_menu_hash'):return
    for k,v in list(s['outbox'].items()):
        if v.get('kind')=='commands' and v['chat']==uid:del s['outbox'][k]
    if len(s['outbox'])>=1900:return
    k=enqueue(s,uid,'',kind='commands')
    s['outbox'][k].update(command_hash=mark,commands=commands,expires=now()+600,priority=1)

def user_help(s,uid):
    if simple_ui(s):return '*Help*\n'+md('API Store — choose an API and confirm its coin price.\nMy APIs — use and manage purchased APIs.\nBuy Credits — choose a pack and pay with Stars.\nInvite & Earn — earn referral coins.\n/freeapi — free starter; /trial — short demo.\n/paysupport — payment or refund issues only.\nKeep API keys private.'),[[btn('API Store','create'),btn('Buy Credits','buy')],[btn('Home','home')]]
    st=s['settings']
    text='*💙 User help*\n\n'+md('Getting started\n/start — your dashboard\n/trial or /demo — one-time timed API trial\n/verify — check all required channel/group joins\n/id — your Telegram ID\n\nAPIs\n/buyapi or /create — choose API type, preview and confirm its price\n/apis — view, edit, pause, renew or delete your APIs\n/stats — your usage and daily quota\n\nWallet and referrals\n/referral — your invite link and API referral estimates\n/wallet — coins, diamonds and available conversion\n/redeem CODE — claim a gift code once\n/buy — configured Telegram Stars packs\n/terms and /paysupport — purchase terms and support')
    text+='\n\n'+md(f"Trial: {st['trial_minutes']} minutes and {st['trial_requests']} total requests on an admin-approved trial source. One claim per Telegram account. Pausing, deleting and rotating keys do not restart it. No wallet debit.\n")
    text+='\n\n'+md(f"Eligible referral: you earn {st['referral_reward']} coins; your new friend earns {st['referral_new_user_reward']} coins after all required joins and activation. Paid daily quotas reset at 00:00 UTC; trial budgets never reset. Accepted upstream attempts consume quota, including failures.")
    text+='\n\n'+md('Daily announcements are automatic after /start. To stop message delivery, block this bot in Telegram. Previous disabled-message preferences are respected.\n/cancel — leave a wizard\nNever share your login codes or API keys. Use only data/APIs you are authorized to access.')
    return text,[[btn('🛒 Buy API','create','success'),btn('My APIs','apis')],
                 [btn('Wallet','wallet'),btn('Referral link','refs')],[btn('Home','home')]]

def admin_help(s,uid):
    actor(s,uid,admin=True)
    text='*🛠 Admin help*\n\n'+md('/admin — admin controls, users, logs and pending referrals\n/adminstats — workspace daily statistics\n/panel — full CRUD panel\n/confirm — fresh confirmation for protected changes\n\nWelcome and campaigns\n/setwelcome — send a selected photo\n/setvideo — send an original welcome video\n/dashboard — dynamic welcome without a separate sticker\n/botstyle — appearance and previews\n/setmessage — capture Telegram-formatted welcome\n/setwelcomemd — set a Markdown welcome\n/setcampaign CAMPAIGN_ID — capture campaign formatting\n/cancel — leave an admin wizard')
    if role(uid,s)=='superadmin':
        text+='\n\n'+md('Owner controls\n/operations — manually customize force-join, private logs, heartbeat and quota warnings\n/setbuttonemoji all — one custom emoji for all buttons; primary/success/danger set individual colours\n/backup — queue an encrypted database snapshot\nRoles and wallet policy are managed in the protected web panel. Firebase owner UIDs and credentials stay in private server CONFIG.')
    text+='\n\n'+md('/adminapis — all customer endpoints; edit limits/auth\n/loghere — owner: send in private logs group with bot admin\n/sources — list source IDs\n/addsource — guided source publishing\n/addplan SOURCE_ID Name | COINS | DAYS | DAILY | RPM | TOTAL\n/dashboard — dynamic dashboard, no sticker\n/setvideo — upload your original welcome video\nOwner: /addcredit USER_ID COINS UNIQUE_REFERENCE\nOwner: /createredeem COINS MAX_USERS DAYS\nOwner: /revokeredeem RECORD_ID')
    text+='\n\n'+md('/broadcast — draft, private preview, one-time/daily schedule and confirmation. /logs — owner verifies private logs.\nThe bot must be admin in required groups/channels and the private log destination. Verify the log destination in Operations. Backups and scheduled messages require the running embedded worker or an authenticated external scheduler. New users join the broadcast audience on /start; historical exclusions and Telegram blocks are respected. Custom emoji support depends on Telegram eligibility; sticker files are not button icons.')
    return text,[[btn('Admin controls','admin'),btn('Admin stats','adminstats')],[btn('Same emoji on all buttons','captureicon:all')],[btn('Appearance','botstyle')]]

def firebase_public_config():
    raw=cfg('FIREBASE_WEB_CONFIG')
    try:raw=json.loads(raw) if isinstance(raw,str) and raw else raw
    except (TypeError,ValueError):raw={}
    allowed=('apiKey','authDomain','databaseURL','projectId','storageBucket','messagingSenderId','appId','measurementId')
    result={k:v for k,v in (raw or {}).items() if k in allowed and isinstance(v,str) and len(v)<=500} if isinstance(raw,dict) else {}
    if cfg('FIREBASE_WEB_API_KEY'):result['apiKey']=str(cfg('FIREBASE_WEB_API_KEY'))
    if cfg('FIREBASE_DATABASE_URL'):result['databaseURL']=str(cfg('FIREBASE_DATABASE_URL'))
    if cfg('FIREBASE_PROJECT_ID'):result['projectId']=str(cfg('FIREBASE_PROJECT_ID'))
    return result


# Telegram bot uses MarkdownV2 and native coloured inline keyboards.
def dashboard_text(s,uid):
    u=s['users'][uid];st=s['settings'];prices=[]
    for source in s['catalog'].values():
        if not source.get('enabled'):continue
        if source.get('plans'):prices.extend(p['price'] for p in source['plans'] if p.get('enabled',True))
        elif source.get('billing_currency','coins')=='coins':prices.append(api_price(s,source)[1])
    goal=min(prices) if prices else st['default_api_price'];balance=u.get('coins',0)
    active=sum(a['owner']==str(uid) and a['active'] and a['expires']>now() and not (a.get('is_trial') and a['calls']>=a['trial_limit']) and not (a.get('total_limit') and a['calls']>=a['total_limit']) for a in s['apis'].values())
    paid=any(a['owner']==str(uid) and not a.get('is_trial') and a['active'] and a['expires']>now() for a in s['apis'].values())
    status='ADMIN' if is_admin(uid,s) else 'PAID PLAN' if paid else 'FREE USER'
    filled=min(10,max(0,balance*10//max(1,goal)));needed=max(0,goal-balance)
    return md(f"👋 Hello, {u['name']}!\n\n╭──〔 💙 API DASHBOARD 〕\n│ 👤 ID: {uid}\n│ 💰 Coins: {balance}\n│ 🎁 Referrals: {u.get('refs',0)}\n│ 🔑 Active APIs: {active}\n│ ⭐ Status: {status}\n╰────────────────\n\n[{'▰'*filled}{'▱'*(10-filled)}] {balance}/{goal} coins\n"+(f"Need {needed} coins for the lowest-priced coin plan." if needed else 'Ready to choose an API plan!')+'\n\nChoose source → plan → preview → buy.\nDeveloper: @DroidDeveloper')

def menu(s,uid):
    if simple_ui(s):return simple_home(s,uid)
    u=s['users'][uid]
    text=dashboard_text(s,uid) if s['settings'].get('welcome_dashboard') else md('💙 Welcome')
    rows=[[btn('🛒 Buy API','create','success'),btn('🔑 My APIs','apis')],
          [btn('💎 Wallet / Buy','wallet','success'),btn('🎁 Referrals','refs')],
          [btn('⏱ Free API trial','trial','success'),btn('📊 Usage','mystats')],
          [btn('Help','help'),btn('Developer','developer')]]
    rows.append([btn('🎟 Redeem code','redeem'),btn('Owner support'+(' · '+str(s.get('support_threads',{}).get(str(uid),{}).get('unread_user',0))+' unread' if focused_ui(s) and s.get('support_threads',{}).get(str(uid),{}).get('unread_user') else ''),'paysupport')])
    if not u.get('active'):rows.insert(0,[btn('Activate account','activate','success')])
    if is_admin(uid,s):rows.append([btn('Admin controls','admin'),btn('Admin web panel','panel')])
    if not focused_ui(s) or is_admin(uid,s):rows.append([btn('All buttons','commands:0'),btn('Delivery format','delivery')])
    if focused_ui(s):
        rows.insert(1,[btn('Prices / ask owner','ownerbuy','success')])
        if str(uid) in SUPER_IDS:rows.append([btn('Customer inbox · '+str(sum(t.get('unread_owner',0) for t in s.get('support_threads',{}).values()))+' unread','supportinbox')])
    if s['settings']['starter_enabled']:rows.insert(2,[btn('10-day free API','starter','success')])
    return text,rows

def source_preview(source):
    if source.get('mode')=='validation':sample=validation_result(source['validator'],source.get('example_value',''))
    elif 'demo_response' in source:sample=source['demo_response']
    elif source.get('mode')=='static':sample=source.get('data')
    else:return md('No synthetic sample saved yet. Admin can add Demo response in the catalogue. No live upstream request was made.')
    text=json.dumps({'ok':True,'data':sample},ensure_ascii=False,separators=(',',':'))
    if len(text)>1400:return md('Sample too large. Admin can save a smaller synthetic demo_response in the catalogue.')
    return '*Demo response — sample only*\n'+code(text)+'\n'+md('Illustration only; usage/expiry metadata omitted. This preview does not spend coins, API quota or your one-time trial.')

def bot_catalogue(s,uid,page=0):
    """Only public source labels/prices go to customers; no upstream URLs/credentials."""
    require(type(page) is int and 0<=page<=999999,'Invalid catalogue page.')
    sources=[(cid,c) for cid,c in s['catalog'].items() if c.get('enabled') and (not c.get('plans') or any(p.get('enabled',True) for p in c['plans']))]
    sources.sort(key=lambda pair:(pair[1]['name'].casefold(),pair[0]))
    size=8;pages=max(1,(len(sources)+size-1)//size);page=min(page,pages-1)
    text='*🛒 Buy API*\n'+md((f'{len(sources)} sources · Page {page+1}/{pages}\nSelect a source, then confirm. You receive your own URL and API key.' if sources else 'No sources available yet. Please check back later.'))
    rows=[]
    for cid,c in sources[page*size:(page+1)*size]:
        currency,price=api_price(s,c)
        if c.get('plans'):
            available=[p for p in c['plans'] if p.get('enabled',True)]
            if not available:continue
            currency='coins';price=min(p['price'] for p in available)
        rows.append([btn(c['name'][:40]+' · '+str(price)+' '+currency,'catalog:'+cid,'success')])
    nav=[]
    if page:nav.append(btn('← Previous','catalogpage:'+str(page-1)))
    if page+1<pages:nav.append(btn('Next →','catalogpage:'+str(page+1)))
    if nav:rows.append(nav)
    if is_admin(uid,s) or (s['settings']['allow_custom'] and not simple_ui(s)):rows.append([btn('Custom API (advanced)','customcreate')])
    if simple_ui(s):
        free=[]
        if s['settings']['starter_enabled']:free.append(btn('Free starter','starter'))
        if s['settings']['trial_enabled']:free.append(btn('Short demo','trial'))
        if free:rows.append(free)
    rows.append([btn('My APIs','apis'),btn('Home','home')])
    return text,rows

def api_keyboard(a):
    i=a["id"]
    if a.get('is_starter'):
        return [[btn('Upgrades / custom key','upgrades:'+i,'success'),btn('Rotate key','rotatecheck:'+i)],
                [btn('Pause' if a['active'] else 'Enable','toggle:'+i),btn('Rename','rename:'+i)],
                [btn('Delete','deletecheck:'+i,'danger'),btn('Back','apis')]]
    if a.get('is_trial'):
        return [[btn('Pause' if a['active'] else 'Enable','toggle:'+i,'danger' if a['active'] else 'success'),btn('Rotate key','rotatecheck:'+i)],
                [btn('Rename','rename:'+i),btn('Delete','deletecheck:'+i,'danger')],[btn('Paid API catalogue','create'),btn('Back','apis')]]
    return [[btn("Pause" if a["active"] else "Enable","toggle:"+i,"danger" if a["active"] else "success"),btn("Edit","edit:"+i)],
       [btn("Renew","renewcheck:"+i,"success"),btn("Rotate key","rotatecheck:"+i)],
       [btn("Rename","rename:"+i),btn("Delete","deletecheck:"+i,"danger")],[btn("Custom key","upgrades:"+i),btn("Back","apis")]]

def issue_login(s,uid):
    require_web_admin(s,uid)
    security_notice(s,'panel_code',uid,'panel')
    token=secrets.token_urlsafe(24)
    for k in list(s["login_codes"]):
        if s["login_codes"][k]["expires"]<now() or s["login_codes"][k]["uid"]==uid: del s["login_codes"][k]
    s["login_codes"][digest(token)]={"uid":uid,"expires":now()+300}
    return token

def command_number(raw,label,low=1,high=1000000):
    require(isinstance(raw,str) and bool(re.fullmatch(r'[0-9]{1,9}',raw)),label+': send a whole number.')
    return integer(int(raw),label,low,high)

def source_wizard(s,uid,raw):
    actor(s,uid,admin=True);f=s['users'][uid]['flow'];require(f.get('t',0)+900>now(),'Source setup expired; use /addsource again.')
    d=f['draft'];step=f['step'];rows=[[btn('Cancel','home')]]
    if step=='source_name':
        require(1<=len(raw)<=60,'Name: 1–60 characters.');d['name']=raw;f['step']='source_url'
        text='Send an authorized non-personal HTTPS source URL, or type phone_format / aadhaar_checksum for an offline validator. Host approval is still required; never send a session or a private record.'
    elif step=='source_url':
        if raw in ('phone_format','aadhaar_checksum'):
            d.update(mode='validation',validator=raw,example_value='0000000000' if raw=='phone_format' else '000000000000')
        else:d.update(mode='proxy',url=raw)
        source_validate({**d,'param':'value'},s['settings']);f['step']='source_param';text='Send the input query name, e.g. value. It must match the provider documentation; key is reserved for your customer authentication.'
    elif step=='source_param':
        d['param']=raw;source_validate(d,s['settings']);f['step']='source_example';text='Send a clearly synthetic public example value (max 200 characters). No credentials or real personal records.'
    elif step=='source_example':
        d['example_value']=raw;source_validate(d,s['settings']);f['step']='source_sample';text='Send a small synthetic JSON sample, or type skip. This is a saved illustration, not a live lookup.'
    elif step=='source_sample':
        if raw.lower()!='skip':d['demo_response']=strict_json(raw)
        source_validate(d,s['settings']);f['step']='source_price';text='Send the default coin price (1–1000000). Add multiple plans after saving with /addplan or the admin page.'
    elif step=='source_price':
        d['price']=command_number(raw,'Price',1,1000000);d.update(enabled=True,billing_currency='coins',trial_enabled=False)
        f['step']='source_confirm';text=f"Publish {d['name']}? Default price: {d['price']} coins. No provider request has been made. Trial remains off until explicitly enabled."
        rows=[[btn('Publish source','sourceconfirm','success'),btn('Cancel','home')]]
    else:raise Problem('Use the confirmation button or /cancel.')
    return md(text),rows

def save_welcome_video(s,uid,message):
    u=actor(s,uid,admin=True);f=u.get('flow',{})
    require(f.get('step')=='welcome_video' and f.get('t',0)+600>now(),'Use /setvideo first.')
    video=message.get('video') or {};fid=video.get('file_id','')
    require(isinstance(fid,str) and re.fullmatch(r'[A-Za-z0-9_-]{10,512}',fid),'Send an actual Telegram video, not a screenshot or document.')
    require(type(video.get('file_size',0)) is int and 0<=video.get('file_size',0)<=20*1024*1024,'Use a video up to 20 MB.')
    s['settings'].update(welcome_video=fid,welcome_photo='',welcome_sticker='',welcome_sticker_info={});clear_welcome_stickers(s)
    u['flow']={};check_data_capacity(s);audit(s,uid,'welcome.video','Telegram video selected')
    return 'Welcome video saved. /start previews it; /dashboard restores the dynamic text caption. No separate sticker is sent.'

# v4.15: bounded owner approvals, starter access and user-controlled credential delivery.
def v415_enabled(s):return bool(s['settings'].get('modern_controls'))

def credential_key(s,label=''):
    if label:
        require(re.fullmatch(r'[A-Za-z][A-Za-z0-9_]{0,15}',label),'Key label: 1–16 letters/digits/underscore, starting with a letter.')
        return 'Droidx'+label+'_'+secrets.token_urlsafe(18)
    if s['settings'].get('key_style')=='droid15':
        alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
        return 'Droid'+''.join(secrets.choice(alphabet) for _ in range(10))
    return 'srd_'+secrets.token_urlsafe(24)

def starter_policy(s):
    st=s['settings'];return {k:st[k] for k in ('starter_days','starter_daily','starter_rpm')}

def starter_menu(s,uid):
    claim=s['starter_claims'].get(str(uid));st=s['settings']
    if claim:
        aid=claim['api_id'];a=s['apis'].get(aid)
        return md('Your one-time free starter was claimed. It cannot be reclaimed by deleting an API. Use referral coins for optional upgrades; the short demo is separate.'),([[btn('Manage starter','api:'+aid)]] if a and a['owner']==str(uid) else [])+[[btn('Earn referral coins','refs'),btn('Home','home')]]
    text=md(f"One free API per Telegram account · {st['starter_days']} days · {st['starter_daily']}/day · {st['starter_rpm']}/minute. The clock starts on confirmation. Separate from the short demo. Choose an eligible source.")
    sources=[c for c in s['catalog'].values() if c.get('enabled') and c.get('starter_enabled',False)] if st['starter_enabled'] else []
    return text+('' if sources else '\n'+md('The owner has not enabled a starter source yet.')),[[btn(c['name'],'starterpick:'+c['id'],'success')] for c in sources[:30]]+[[btn('Short demo','trial'),btn('Home','home')]]

def create_starter(s,uid,data):
    uid=str(uid);u=actor(s,uid);st=s['settings']
    require(st['starter_enabled'] and uid.isdigit() and (u.get('telegram_started') or DEMO),'Starter access unavailable.',403)
    require(u.get('active') and joined(s,uid),'Activate and verify all required joins first.',403,'JOIN_REQUIRED')
    require(not u.get('wallet_hold'),'Resolve your wallet hold first.',403)
    require(uid not in s['starter_claims'],'Free starter already claimed.',409,'STARTER_USED')
    require(len(s['starter_claims'])<3000 and sum(a['owner']==uid for a in s['apis'].values())<st['max_apis'],'API/account capacity reached.',409)
    require(isinstance(data,dict) and set(data)=={'catalog_id','quote'} and data['quote']==starter_policy(s),'Starter policy changed. Select again.',409)
    cid=data['catalog_id'];src=s['catalog'].get(cid)
    require(src and src.get('enabled') and src.get('starter_enabled'),'Source not eligible for free starter.',403)
    if src['mode'] in ('proxy','validation'):require(src.get('example_value'),'Owner must configure a public example first.')
    aid=new_id('api_');key=credential_key(s);deadline=now()+st['starter_days']*86400
    a={'id':aid,'owner':uid,'name':clip_text(src['name'],42)+' · Free starter','mode':'catalog','catalog_id':cid,'key_hash':digest(key),
       'active':True,'public':False,'header_only':bool(st['default_header_only']),'is_starter':True,'billing_currency':'coins','price':st['starter_extend_price'],
       'daily':st['starter_daily'],'rpm':st['starter_rpm'],'expires':deadline,'created':now(),'calls':0,'errors':0,'day':utc_day(),'used':0,'minute':0,'minute_used':0,'history':[]}
    s['apis'][aid]=a;s['starter_claims'][uid]={'api_id':aid,'catalog_id':cid,'claimed_at':now(),'expires':deadline}
    check_data_capacity(s);audit(s,uid,'api.starter.create',aid)
    return {'id':aid,'key':key,'name':a['name'],'expires':deadline,'daily':a['daily'],'rpm':a['rpm'],**api_links(s,a,key)}

def upgrade_quote(s,kind):
    st=s['settings'];require(kind in ('extend','quota','customkey'),'Unknown upgrade.')
    return {'kind':kind,'price':st[{'extend':'starter_extend_price','quota':'starter_quota_price','customkey':'custom_key_price'}[kind]],
            'amount':st['starter_extend_days'] if kind=='extend' else st['starter_quota_add'] if kind=='quota' else 0}

def upgrade_api(s,uid,aid,d):
    a=owned(s,uid,aid);u=actor(s,uid);kind=d.get('kind');quote=upgrade_quote(s,kind)
    require(a['owner']==str(uid),'Upgrade from the owning account.',403)
    require(d.get('quote')==quote,'Upgrade price changed. Confirm again.',409)
    require(joined(s,uid) and not u.get('wallet_hold'),'Verify joins / resolve wallet hold first.',403)
    require(not a.get('is_trial'),'Short demo budgets cannot be upgraded; use a paid or starter API.',409)
    if kind!='customkey':require(a.get('is_starter'),'This upgrade is only for the free starter API.')
    if kind=='customkey':
        label=str(d.get('label',''));key=credential_key(s,label)
    if kind=='extend':require(max(a['expires'],now())+quote['amount']*86400<=now()+365*86400,'Maximum one-year remaining validity.')
    if kind=='quota':require(a['daily']+quote['amount']<=100000,'Daily quota maximum reached.')
    wallet_change(s,uid,'coins',-quote['price'],'API upgrade '+kind,aid)
    if kind=='extend':a['expires']=max(now(),a['expires'])+quote['amount']*86400
    elif kind=='quota':a['daily']+=quote['amount']
    else:
        a.update(key_hash=digest(key),key_label=label)
        audit(s,uid,'api.key.customize',aid)
        return {'id':aid,'key':key,'name':a['name'],'expires':a['expires'],'daily':a['daily'],**api_links(s,a,key)}
    audit(s,uid,'api.upgrade',aid);return {'message':'Upgrade applied. Usage counters were not reset.'}

def safe_chat_credentials(result):
    p=urllib.parse.urlsplit(result['request_url'])
    host=(p.hostname or '')+((':'+str(p.port)) if p.port else '')
    return '\n'.join(['PRIVATE API CREDENTIALS — do not forward','Name: '+str(result.get('name','API')),
        'Protocol: '+p.scheme,'Host (remove spaces): '+host.replace('.', ' . '),'Path: '+p.path,
        'Query (without key): '+(p.query or '(none)'),'X-API-Key: '+result['key'],
        'Use the header, not a keyed chat link. This message contains no clickable API URL.'])

def credential_delivery_mode(s,uid):
    preferred=s['users'].get(str(uid),{}).get('receipt_mode','default')
    if focused_ui(s) and not is_admin(uid,s):preferred='default'
    if preferred in ('txt','text'):return preferred
    return 'txt' if s['settings'].get('api_receipts_txt') else 'text'

def use_safe_receipt(s,uid):
    return v415_enabled(s) or s['settings'].get('api_receipts_txt') or s['settings'].get('safe_chat_receipts') or s['users'].get(str(uid),{}).get('receipt_mode') in ('txt','text')

def command_buttons(s,uid,page=0):
    commands=commands_for(s,uid);size=10;pages=max(1,(len(commands)+size-1)//size);page=min(max(0,page),pages-1)
    rows=[[btn('/'+c['command'],'cmd:'+c['command']) for c in commands[i:i+2]] for i in range(page*size,min(len(commands),(page+1)*size),2)]
    nav=[]
    if page:nav.append(btn('← Back','commands:'+str(page-1)))
    if page+1<pages:nav.append(btn('More →','commands:'+str(page+1)))
    if nav:rows.append(nav)
    rows.append([btn('Home','home')])
    return md('All '+('admin' if is_admin(uid,s) else 'user')+' controls · '+str(page+1)+'/'+str(pages)+'\nSelect a button. Parameter-based actions guide you through the required input.'),rows

# Exact-operation approvals. Stored payloads for bot drafts are encrypted, never copied into logs.
def approval_summary(scope,data):
    safe={}
    for k in ('id','user_id','uid','coins','amount','role','daily','rpm','days','price','enabled','blocked','log_channel','owner_approval_required','starter_enabled','default_header_only','confirm','file_sha256','file_bytes'):
        v=data.get(k)
        if type(v) in (int,bool) or isinstance(v,str) and re.fullmatch(r'[A-Za-z0-9_:\-]{1,80}',v):safe[k]=v
    for k,v in data.items():
        if k in DEFAULTS and type(DEFAULTS[k]) in (int,bool) and type(v) in (int,bool):safe[k]=v
    plans=data.get('plans',[]) if isinstance(data.get('plans',[]),list) else []
    if isinstance(data.get('plan'),dict):plans=[data['plan']]
    prices=[{k:p[k] for k in ('price','days','daily','rpm','enabled') if k in p and type(p[k]) in (int,bool)} for p in plans[:2] if isinstance(p,dict)]
    if prices:safe['plan_terms']=prices
    text=scope+'\nFields: '+', '.join(sorted(str(k) for k in data))[:200]
    if safe:text+='\n'+json.dumps(safe,ensure_ascii=False)[:400]
    return text

def prune_approvals(s):
    for k,a in list(s['approvals'].items()):
        if a['expires']<=now() and a['status'] in ('pending','approved'):a['status']='expired'
        if a['expires']+86400<now():del s['approvals'][k]

def new_approval(s,uid,scope,payload,session_hash='',kind='web'):
    actor(s,uid,admin=True);prune_approvals(s)
    require(SUPER_IDS,'Configure a Telegram superadmin in hosting code first.',503)
    fingerprint=digest(json.dumps([scope,payload],sort_keys=True,separators=(',',':'),ensure_ascii=False))
    for k,a in s['approvals'].items():
        if a['uid']==str(uid) and a['session_hash']==session_hash and a['fingerprint']==fingerprint and a['kind']==kind and a['status'] in ('pending','approved') and a['expires']>now():return k,[]
    require(sum(a['status']=='pending' for a in s['approvals'].values())<100 and len(s['approvals'])<300,'Approval capacity reached; review pending requests.',429)
    require(sum(a['uid']==str(uid) and a['created']>now()-60 for a in s['approvals'].values())<6,'Too many approval requests. Wait a minute.',429)
    key=new_id('apr_');summary=approval_summary(scope,payload)
    a={'id':key,'uid':str(uid),'scope':scope,'fingerprint':fingerprint,'session_hash':session_hash,'kind':kind,'status':'pending','created':now(),'expires':now()+600,'summary':summary}
    if kind=='bot':a['payload_enc']=fernet().encrypt(json.dumps(payload,ensure_ascii=False).encode()).decode()
    s['approvals'][key]=a;jobs=[]
    for owner in sorted(SUPER_IDS):
        k=soft_message(s,owner,'*Owner approval needed*\n'+md('Requester: '+str(uid)+'\n'+summary+'\nExpires in 10 minutes. Approve only an action you recognize.'),[[btn('Approve','approve:'+key,'success'),btn('Reject','reject:'+key,'danger')]],kind='approval')
        if k:s['outbox'][k].update(priority=-20,approval_id=key);jobs.append(k)
    audit(s,uid,'approval.request',key);return key,jobs

def decide_approval(s,uid,key,approve):
    require(str(uid) in SUPER_IDS,'Only the configured Telegram owner can decide.',403);actor(s,uid,superonly=True)
    a=s['approvals'].get(key);require(a and a['status']=='pending' and a['expires']>now(),'Approval is no longer pending.',409)
    actor(s,a['uid'],admin=True)
    if a['kind']=='web':
        rec=s['sessions'].get(a['session_hash']);require(rec and rec['uid']==a['uid'] and rec['expires']>now(),'Requester session expired/revoked.',409)
    a.update(status='approved' if approve else 'rejected',decided_by=str(uid),decided_at=now())
    if approve and a['kind']=='bot':
        d=json.loads(fernet().decrypt(a['payload_enc'].encode()))
        if a['scope']=='broadcast':publish_bot_broadcast(s,uid,d)
        elif a['scope']=='catalog':admin_action(s,uid,'catalog',d)
        elif a['scope']=='api_limits':api_action(s,uid,d.pop('id'),'edit',d)
        elif a['scope']=='plan':
            src=s['catalog'].get(d['id']);require(src,'Source deleted.',409)
            src['plans']=validate_source_plans(src.get('plans',[])+[d['plan']]);check_data_capacity(s);audit(s,uid,'catalog.plan.add',d['id'])
        else:raise Problem('Unsupported bot approval.')
        a['status']='completed';a.pop('payload_enc',None)
    audit(s,uid,'approval.'+a['status'],key)
    return 'Approved. The bound web request may now execute once.' if a['status']=='approved' else 'Approved and applied.' if a['status']=='completed' else 'Rejected. No action executed.'

def web_approval_required(s,uid):
    if not s['settings'].get('owner_approval_required') or DEMO:return False
    endpoint=request.endpoint or ''
    if endpoint=='export_route' and request.method=='GET':return True
    if request.method!='POST':return False
    if endpoint in ('backup_route','restore_route'):return True
    if endpoint=='admin_route':return True
    if endpoint in ('operations_route','campaign_save_route','campaign_action_route','engagement_settings_route','payment_admin_route'):return True
    if endpoint=='api_action_route':
        a=s['apis'].get((request.view_args or {}).get('aid',''),{})
        return a.get('owner')!=str(uid) or bool((request.get_json(silent=True) or {}).get('public'))
    return False

def authorize_web_approval(uid):
    if request.endpoint=='restore_route':
        file=request.files.get('file');require(file is not None and request.form.get('confirm')=='RESTORE','Select an encrypted backup and type RESTORE.')
        pos=file.stream.tell();blob=file.read();file.stream.seek(pos)
        payload={'confirm':'RESTORE','file_sha256':hashlib.sha256(blob).hexdigest(),'file_bytes':len(blob)}
    else:payload={} if request.method=='GET' else body()
    scope=request.method+' '+request.path;require(len(scope)<=256,'Action path too long.')
    sid=digest(session['sid']);requested=request.headers.get('X-Owner-Approval','')
    fingerprint=digest(json.dumps([scope,payload],sort_keys=True,separators=(',',':'),ensure_ascii=False))
    def prepare(s):
        check_web_session(s,uid);actor(s,uid,admin=True)
        if requested:
            a=s['approvals'].get(requested)
            require(a and a['kind']=='web' and a['uid']==uid and a['session_hash']==sid and a['fingerprint']==fingerprint and a['scope']==scope,'Approval does not match this action/session.',403)
            require(a['status']=='approved' and a['expires']>now(),'Approval is not approved, expired, or already used.',409)
            require(a.get('decided_by') in SUPER_IDS,'Approver is no longer configured.',403)
            a['status']='executing';return requested,[]
        return new_approval(s,uid,scope,payload,sid)
    key,jobs=store.tx(prepare)
    if requested:
        g.owner_approval={'uid':uid,'sid':sid,'id':key};return None
    for keyjob in jobs[:2]:drain(1,3,job_id=keyjob)
    return jsonify(error='OWNER_APPROVAL_REQUIRED',message='Open the owner bot DM and approve this exact request. This page will resume automatically.',approval_id=key),428

@app.get('/manage/approvals/<key>')
@protected(admin=True)
def approval_status_route(uid,key):
    s=store.read();a=s['approvals'].get(key);require(a and a['uid']==uid and a['session_hash']==digest(session['sid']),'Approval not found for this session.',404)
    return jsonify(status='expired' if a['expires']<=now() and a['status'] in ('pending','approved') else a['status'],expires=a['expires'],summary=a['summary'])

def publish_bot_broadcast(s,uid,draft):
    actor(s,uid,superonly=True);formatted_template(draft['text'],'entities',draft['entities'])
    result=save_campaign(s,uid,{'name':'Bot broadcast '+str(now()),'text':draft['text'],'trigger':draft['trigger'],'min_hours':24,'max_hours':24,'enabled':True})
    s['campaigns'][result['id']].update(text=draft['text'],text_mode='entities',text_entities=draft['entities']);s['settings']['campaigns_enabled']=True
    audit(s,uid,'broadcast.approved',result['id']);return result

# v4.16: focused navigation, owner inquiries and encrypted two-way support.
def focused_ui(s):return bool(s['settings'].get('focused_bot_ui'))

def valid_nav(anchor):return isinstance(anchor,dict) and type(anchor.get('id')) is int and 0<anchor['id']<2**31

def recover_bot_screen(s,uid):
    # Explicit typed /start or /admin may recover a screen hidden far up the chat.
    # Callbacks/wizard input never create a recovery screen. At most once per minute.
    u=s['users'][str(uid)]
    if u.get('nav_recovery_pending') or u.get('nav_recovery_at',0)+60>now() or not valid_nav(u.get('bot_nav')):return False
    u['nav_epoch']=u.get('nav_epoch',0)+1;u['nav_recovery_at']=now();u['nav_recovery_pending']=True
    u.pop('bot_nav',None)
    # Old leased jobs may finish, but cannot re-install their obsolete anchor.
    for key,job in list(s['outbox'].items()):
        if job.get('chat')==str(uid) and job.get('nav') and job.get('lease',0)<=now() and not job.get('receipt'):del s['outbox'][key]
    return True

def nav_job(s,key,uid,update=None):
    j=s['outbox'].get(key);u=s['users'].get(str(uid))
    if not j or not u or j.get('kind') not in ('message','photo') or j.get('receipt') or j.get('reply_keyboard'):return
    j.update(nav=True,priority=-10,nav_epoch=u.get("nav_epoch",0))
    # Only ordinary bot screens. Requested media previews and security/financial receipts are separate.
    if j.get('explicit_preview'):j.pop('nav',None);return
    anchor={} if u.get('nav_recovery_pending') else u.get('bot_nav',{})
    if u.get('nav_recovery_pending'):
        j.pop('edit_message_id',None);j.pop('edit_caption',None);j.pop('photo',None);j.pop('video',None);j['kind']='message'
    if not valid_nav(anchor) and update and not u.get('nav_recovery_pending'):
        target=callback_edit_target(update,j)
        if target:anchor={'id':target['edit_message_id'],'caption':target.get('edit_caption',False)}
    if valid_nav(anchor):
        # A text anchor cannot become a photo without a new message; keep the persistent screen text-only.
        j.pop('photo',None);j.pop('video',None);j['kind']='message'
        if not anchor.get('caption') or j.get('screen_units',text_units(j['text']))<=1024:
            j.update(edit_message_id=anchor['id'],edit_caption=bool(anchor.get('caption')))
        else:j['needs_text_anchor']=True # one-time caption -> text migration for long screens
    for previous,old in list(s['outbox'].items()):
        if previous!=key and old.get('nav') and old.get('chat')==str(uid) and old.get('lease',0)<=now() and not old.get('receipt'):
            del s['outbox'][previous]

def support_thread(s,viewer,target,create=False):
    actor(s,viewer);target=str(target)
    require(str(viewer)==target or str(viewer) in SUPER_IDS,'Private conversation: access denied.',403)
    require(target.isdigit() and target in s['users'] and not s['users'][target].get('blocked'),'Customer unavailable.',404)
    threads=s.setdefault('support_threads',{})
    if target not in threads:
        require(create,'Conversation not found.',404)
        require(SUPER_IDS,'Owner contact is not configured.',503)
        for key,t in list(threads.items()):
            if t.get('closed') and t.get('updated',0)+7*86400<now():del threads[key]
        require(len(threads)<100,'Support inbox is full. Please contact the configured owner username.',429)
        threads[target]={'uid':target,'created':now(),'updated':now(),'closed':False,'messages':[],'unread_owner':0,'unread_user':0,'revision':0}
    return threads[target]

def support_append(s,sender,target,text,system=False):
    require(not simple_ui(s),'General support chat is disabled.',403)
    thread=support_thread(s,sender,target,create=True)
    require(not thread['closed'],'Conversation closed. Reopen it first.',409)
    require(isinstance(text,str) and 1<=text_units(text)<=600,'Send text up to 600 UTF-16 units. Do not send passwords or API keys.')
    u=s['users'][str(sender)];stamp=now()
    if not system:
        rate=u.setdefault('support_rate',{'minute':stamp//60,'count':0})
        if rate['minute']!=stamp//60:rate.update(minute=stamp//60,count=0)
        require(rate['count']<8,'Support rate limit: please wait a minute.',429);rate['count']+=1
    owner=str(sender) in SUPER_IDS and str(sender)!=str(target)
    thread['messages'].append({'t':stamp,'sender':str(sender),'owner':owner,'body_enc':fernet().encrypt(text.encode()).decode()})
    thread['messages']=thread['messages'][-24:];thread['updated']=stamp;thread['revision']+=1
    field='unread_user' if owner else 'unread_owner';thread[field]=min(999,thread.get(field,0)+1)
    require(len(json.dumps(s['support_threads']).encode())<=512*1024,'Support history capacity reached. Close old conversations before adding more.',429)
    audit(s,sender,'support.reply' if owner else 'support.message',str(target))
    return thread

def support_screen(s,viewer,target,page=0):
    t=support_thread(s,viewer,target);owner=str(viewer) in SUPER_IDS and str(viewer)!=str(target)
    messages=t['messages'];pages=max(1,(len(messages)+1)//2);page=max(0,min(page,pages-1))
    end=len(messages)-page*2;shown=messages[max(0,end-2):end]
    text='*💬 Owner support*\n'+md('Customer '+str(target)+' · '+('CLOSED' if t['closed'] else 'OPEN')+f' · History {page+1}/{pages}\nText only: up to 600 UTF-16 units per reply. Recent history: 24 messages. Never send passwords, login codes or API keys.')
    for item in shown:
        try:body=fernet().decrypt(item['body_enc'].encode()).decode()
        except Exception:body='[Message unavailable]'
        text+='\n\n'+md(('Owner' if item['owner'] else 'Customer')+' · '+iso(item['t'])+'\n'+body)
    rows=[];navigation=[]
    if page+1<pages:navigation.append(btn('Older','supportpage:'+str(target)+':'+str(page+1)))
    if page:navigation.append(btn('Newer','supportpage:'+str(target)+':'+str(page-1)))
    if navigation:rows.append(navigation)
    rows.append([btn('Reopen' if t['closed'] else 'Reply','supportopen:'+str(target)) ,btn('Refresh','supportview:'+str(target))])
    if not t['closed']:rows.append([btn('Close conversation','supportclose:'+str(target),'danger')])
    rows.append([btn('Inbox','supportinbox') if owner else btn('Home','home')])
    return text,rows

def support_inbox(s,uid,page=0):
    require(str(uid) in SUPER_IDS,'Configured owner only.',403)
    items=sorted(s.setdefault('support_threads',{}).values(),key=lambda t:(t.get('closed',False),-t.get('unread_owner',0),-t.get('updated',0)))
    pages=max(1,(len(items)+7)//8);page=max(0,min(page,pages-1))
    text='*💬 Customer inbox*\n'+md(f'{len(items)} conversations · Page {page+1}/{pages}\nSelect a customer to read and reply. No payment is confirmed by a support message.')
    rows=[[btn(t['uid']+' · '+('closed' if t['closed'] else 'open')+' · '+str(t.get('unread_owner',0))+' unread','supportview:'+t['uid'])] for t in items[page*8:(page+1)*8]]
    nav=[]
    if page:nav.append(btn('Previous','supportinbox:'+str(page-1)))
    if page+1<pages:nav.append(btn('More','supportinbox:'+str(page+1)))
    if nav:rows.append(nav)
    rows.append([btn('Refresh','supportinbox'),btn('Admin','admin')]);return text,rows

def support_queue(s,viewer,target=None,inbox=False):
    u=s['users'].get(str(viewer))
    if not u or u.get('blocked') or u.get('telegram_blocked') or not u.get('telegram_started'):return
    text,rows=support_inbox(s,viewer) if inbox else support_screen(s,viewer,target)
    key=enqueue(s,viewer,text,rows);j=s['outbox'][key]
    j.update(support_target=None if inbox else str(target),support_private=True)
    nav_job(s,key,str(viewer));seal_support_job(j);return key

def support_notify(s,sender,target):
    recipients=[str(target)] if str(sender) in SUPER_IDS and str(sender)!=str(target) else sorted(SUPER_IDS)
    for uid in recipients:
        u=s['users'].get(uid,{})
        if u.get('flow') and u['flow'].get('step')!='support_chat' and u['flow'].get('t',0)+1800>now():continue
        view=u.get('bot_view','home')
        if view not in ('home','admin','support','supportinbox','paysupport','contactbuy','contacthelp'):continue
        active=u.get('flow',{}).get('target')
        if active and active!=str(target):continue
        support_queue(s,uid,target,inbox=uid in SUPER_IDS and not active)


def owner_buy_menu(s,uid,page=0):
    options=[]
    for cid,src in s['catalog'].items():
        if not src.get('enabled'):continue
        if src.get('plans'):
            for p in src['plans']:
                if p.get('enabled',True):options.append((src['name']+' / '+p['name']+' · '+str(p['price'])+' coins','ownerpick:'+cid+':'+p['id']))
        else:
            currency,price=api_price(s,src);options.append((src['name']+' · '+str(price)+' '+currency,'ownerpick:'+cid+':default'))
    for p in s['settings']['purchase_packs']:
        if p['enabled']:options.append((p['name']+' · '+str(p['stars'])+' Stars','ownerpack:'+p['id']))
    pages=max(1,(len(options)+7)//8);page=max(0,min(page,pages-1))
    text='*🛒 Prices / ask owner*\n'+md(f'Page {page+1}/{pages}\nChoose an item to generate a purchase inquiry. No debit, payment or API activation occurs here. Stars checkout and coin purchases remain separate.')
    rows=[[btn(label[:90],action)] for label,action in options[page*8:(page+1)*8]]
    nav=[]
    if page:nav.append(btn('Previous','ownerbuy:'+str(page-1)))
    if page+1<pages:nav.append(btn('More','ownerbuy:'+str(page+1)))
    if nav:rows.append(nav)
    rows.append([btn('Buy with coins','create'),btn('Stars checkout','wallet')]);rows.append([btn('Support','paysupport'),btn('Home','home')]);return text,rows

def owner_quote(s,action):
    if action.startswith('ownerpack:'):
        pid=action.split(':',1)[1];p=next((p for p in s['settings']['purchase_packs'] if p['id']==pid and p['enabled']),None)
        require(p,'Pack unavailable.',404)
        return {'action':action,'item':p['name'],'price':p['stars'],'currency':'Stars','terms':str(p['amount'])+' '+p['currency']}
    _,cid,pid=action.split(':',2);src=s['catalog'].get(cid);require(src and src.get('enabled'),'Source unavailable.',404)
    if pid!='default':
        p=selected_plan(src,pid);return {'action':action,'item':src['name']+' / '+p['name'],'price':p['price'],'currency':'coins','terms':plan_summary(p)}
    require(not src.get('plans'),'Choose a current plan.',409);currency,price=api_price(s,src)
    st=s['settings'];return {'action':action,'item':src['name'],'price':price,'currency':currency,'terms':f"{st['valid_days']} days · {st['daily_limit']}/day · {st['rpm']}/minute"}


def focused_support_action(s,uid,action,raw,cb):
    u=s['users'][uid]
    if action=='ownerbuy' or action.startswith('ownerbuy:'):
        u['flow']={};return owner_buy_menu(s,uid,int(action.split(':')[1]) if ':' in action else 0)
    if action.startswith(('ownerpick:','ownerpack:')):
        quote=owner_quote(s,action);u['flow']={'step':'owner_quote','quote':quote,'t':now()}
        return '*Purchase inquiry preview*\n'+md(quote['item']+'\nPrice: '+str(quote['price'])+' '+quote['currency']+'\n'+quote['terms']+'\nSend this request to the configured owner? No coins are deducted.'),[[btn('Send to owner','ownerrequest','success'),btn('Cancel','ownerbuy')]]
    if action=='ownerrequest':
        f=u.get('flow',{});require(f.get('step')=='owner_quote' and f['t']+600>now(),'Request expired. Select an item again.',409)
        quote=f['quote'];require(owner_quote(s,quote['action'])==quote,'Price/terms changed. Select again.',409)
        t=support_thread(s,uid,uid,True);t['closed']=False
        message='Purchase inquiry\nCustomer ID: '+uid+'\nI want: '+quote['item']+'\nShown price: '+str(quote['price'])+' '+quote['currency']+'\n'+quote['terms']+'\nPlease help me with the next steps. This is not payment confirmation.'
        support_append(s,uid,uid,message);u['flow']={'step':'support_chat','target':uid,'t':now()};support_notify(s,uid,uid)
        return support_screen(s,uid,uid)
    if action in ('paysupport','contacthelp','contactbuy'):
        if uid in SUPER_IDS:u['flow']={};return support_inbox(s,uid)
        if action=='contactbuy':u['flow']={};return owner_buy_menu(s,uid)
        t=support_thread(s,uid,uid,True);u['flow']={'step':'support_chat','target':uid,'t':now()}
        return support_screen(s,uid,uid)
    if action=='supportinbox' or action.startswith('supportinbox:'):
        u['flow']={};return support_inbox(s,uid,int(action.split(':')[1]) if ':' in action else 0)
    if action.startswith(('supportview:','supportopen:','supportclose:','supportreply:','supportpage:')):
        parts=action.split(':');target=parts[1];t=support_thread(s,uid,target)
        if parts[0]=='supportclose':
            t.update(closed=True,updated=now());u['flow']={};audit(s,uid,'support.close',target);support_notify(s,uid,target)
        else:
            if parts[0] in ('supportopen','supportreply'):t['closed']=False
            u['flow']={'step':'support_chat','target':target,'t':now()}
            t['unread_owner' if uid in SUPER_IDS and uid!=target else 'unread_user']=0
        return support_screen(s,uid,target,int(parts[2]) if parts[0]=='supportpage' else 0)
    if not cb and u.get('flow',{}).get('step')=='support_chat' and not raw.startswith('/'):
        target=u['flow']['target'];support_append(s,uid,target,raw);support_notify(s,uid,target);return support_screen(s,uid,target)
    return None

_BOT_TIMINGS={}
_WORKER_WAKE=threading.Event()
_BACKUP_THREAD=None

def wake_worker():_WORKER_WAKE.set()

def worker_available():
    return not DEMO and not os.environ.get('VERCEL') and _WORKER_THREAD is not None and _WORKER_THREAD.is_alive()

def schedule_backup_async():
    global _BACKUP_THREAD
    if _BACKUP_THREAD is not None and _BACKUP_THREAD.is_alive():return
    def backup_task():
        try:run_backup()
        except Exception:LOG.warning('Background backup failed; no secret details logged')
        finally:wake_worker()
    _BACKUP_THREAD=threading.Thread(target=backup_task,name='srd-backup',daemon=True);_BACKUP_THREAD.start()

def seal_support_job(job):
    if job.get('support_private') and 'private_text_enc' not in job:
        job['screen_units']=text_units(job['text']);job['private_text_enc']=fernet().encrypt(job['text'].encode()).decode();job['text']='Private support screen'

# Native chat picker. Selection is verified outside transactions before confirmation.
def picker_rights():
    return {k:k in ('can_manage_chat','can_invite_users') for k in ('is_anonymous','can_manage_chat','can_delete_messages','can_manage_video_chats','can_restrict_members','can_promote_members','can_change_info','can_invite_users','can_post_stories','can_edit_stories','can_delete_stories')}

def queue_join_picker(s,uid,channel):
    actor(s,uid,superonly=True);rid=secrets.randbelow(2**30)+1
    s['users'][uid]['flow']={'step':'join_pick','request_id':rid,'channel':channel,'t':now()}
    k=enqueue(s,uid,md('Select a channel or group you administer. Telegram needs a temporary selection keyboard for this step. The bot must be an administrator.'))
    s['outbox'][k]['reply_keyboard']={'keyboard':[[{'text':'Choose channel' if channel else 'Choose group','request_chat':{'request_id':rid,'chat_is_channel':channel,'bot_is_member':True,'request_title':True,'request_username':True,'user_administrator_rights':picker_rights(),'bot_administrator_rights':picker_rights()}}]],'resize_keyboard':True,'one_time_keyboard':True}
    return k

def join_setup_probe(v):
    chat=tg('getChat',{'chat_id':v['target']});require(chat.get('type')==('channel' if v['channel'] else 'supergroup') or not v['channel'] and chat.get('type')=='group','Wrong chat type.')
    me=tg('getMe',{});bot=tg('getChatMember',{'chat_id':v['target'],'user_id':me['id']});own=tg('getChatMember',{'chat_id':v['target'],'user_id':int(v['chat'])})
    require(bot.get('status') in ('creator','administrator') and own.get('status') in ('creator','administrator'),'Both you and the bot must administer the selected chat.')
    return {'chat_id':v['target'],'title':str(chat.get('title','Join channel'))[:40],'url':'https://t.me/'+chat['username'] if chat.get('username') else chat.get('invite_link','')}

def finish_join_setup(s,v,result):
    u=actor(s,v['chat'],superonly=True);f=u.get('flow',{})
    require(f.get('step')=='join_probe' and f.get('request_id')==v['request_id'] and f.get('t',0)+600>now(),'Selection expired; choose again.')
    require(result['chat_id']!=s['settings'].get('log_channel'),'Keep required joins separate from private logs.')
    u['flow']={'step':'join_confirm' if result['url'] else 'join_link','draft':result,'t':now()}
    key=soft_message(s,v['chat'],md('Selected: '+result['title']+'\n'+('Confirm adding this required join.' if result['url'] else 'Send its working https://t.me/+… invite link. A private chat ID is not an invite link.')),
                 [[btn('Add required join','joinconfirm','success'),btn('Cancel','home')]] if result['url'] else [[btn('Cancel','home')]])
    nav=u.get('bot_nav',{})
    if key and v415_enabled(s) and nav.get('id') and nav.get('t',0)+86400>now():s['outbox'][key].update(nav=True,edit_message_id=nav['id'],edit_caption=nav.get('caption',False))

_WORKER_THREAD=None
_WORKER_LOCK=threading.Lock()
def background_worker_requested():
    flag=cfg('AUTO_WORKER');return flag is True or str(flag).lower() in ('1','true','yes')

def start_embedded_worker():
    global _WORKER_THREAD
    flag=cfg('AUTO_WORKER')
    if DEMO or os.environ.get('VERCEL') or not store or not (flag is True or str(flag).lower() in ('1','true','yes')):return False
    with _WORKER_LOCK:
        if _WORKER_THREAD and _WORKER_THREAD.is_alive():return True
        _WORKER_THREAD=threading.Thread(target=run_worker,name='srd-delivery-worker',daemon=True);_WORKER_THREAD.start()
    return True



def process_bot(s,update):
    update_id=str(update.get("update_id",""))
    require(update_id.isdigit() and len(update_id)<=19,"Invalid update.")
    system=s["system"]
    # Bounded replay window, including an eviction watermark. An evicted old ID must NOT
    # execute a destructive action again. After >7 days without updates, Telegram may restart
    # its sequence with a random ID, so the old watermark is reset on genuine inactivity.
    previous_update=system.get("last_bot_update",max(s["updates"].values(),default=0))
    if previous_update+7*86400<now():
        s["updates"]={}; system["update_floor"]=-1
    if update_id in s["updates"] or int(update_id)<=system.get("update_floor",-1): return False
    s["updates"][update_id]=now(); system["last_bot_update"]=now()
    expired=[k for k,v in s["updates"].items() if v<now()-7*86400]
    excess=sorted(s["updates"],key=int)[:max(0,len(s["updates"])-8192)]
    evicted=set(expired+excess)
    if evicted:
        system["update_floor"]=max(system.get("update_floor",-1),max(map(int,evicted)))
        for k in evicted: s["updates"].pop(k,None)
    if system.get("security_pruned",0)+60<now():
        prune_security_state(s); system["security_pruned"]=now()
    cb=update.get("callback_query"); m=cb.get("message",{}) if cb else update.get("message",{})
    sender=cb.get("from",{}) if cb else m.get("from",{})
    if (not cb and sender and not sender.get('is_bot') and m.get('chat',{}).get('type') in ('group','supergroup')
        and str(sender.get('id')) in SUPER_IDS and str(m.get('text','')).strip().lower() in ('/start','/start@'+bot_username(s).lower(),'/id','/id@'+bot_username(s).lower())):
        u=s['users'].get(str(sender['id']))
        if not u or u.get('blocked'):return True
        target=str(m['chat']['id']);last=s['system'].get('group_help_at',0)
        if now()-last<10:return True
        s['system']['group_help_at']=now()
        k=soft_message(s,target,md('Bot is responding. Chat ID: '+target+'\nDashboard and admin controls are DM-only. To connect this private admin logs group, make the bot an administrator and send /loghere here from the owner account.'))
        if k:s['outbox'][k]['group_help']=True
        return True
    if (not cb and sender and not sender.get('is_bot') and m.get('chat',{}).get('type') in ('group','supergroup')
        and str(sender.get('id')) in SUPER_IDS and str(m.get('text','')).strip().lower() in ('/loghere','/loghere@'+bot_username(s).lower())):
        owner=str(sender['id']);u=s['users'].get(owner)
        if not u or u.get('blocked') or not u.get('telegram_started'):return True
        if s['system'].get('log_test_at',0)+30>now():return True
        target=str(m['chat']['id'])
        if not re.fullmatch(r'-[0-9]{1,19}',target):return True
        if target in {c['chat_id'] for c in s['settings']['force_join_channels']}:
            soft_message(s,owner,md('Keep private logs separate from required join groups.'));return True
        prune_expired_log_checks(s)
        if any(v.get('kind')=='logverify' and v.get('lease',0)>now() for v in s['outbox'].values()):return True
        for old,j in list(s['outbox'].items()):
            if j.get('kind')=='logverify':del s['outbox'][old]
        k=enqueue(s,owner,'',kind='logverify')
        s['outbox'][k].update(target=target,expires=now()+300,set_destination=True,previous_destination=s['settings'].get('log_channel',''),priority=-2)
        s['system'].update(log_test_at=now(),log_check={'job_id':k,'target':target,'state':'checking','t':now(),'message':'Checking Telegram access now.'})
        soft_message(s,owner,md('Private logs verification requested for '+target+'. The destination changes only after privacy and bot admin permissions are verified.'))
        return True
    if sender and not sender.get('is_bot') and m.get('chat',{}).get('type') in ('group','supergroup'):
        first_group=str(m.get('text','')).split(maxsplit=1)[0].split('@')[0].lower() if m.get('text') else ''
        if first_group in ('/panel','/planel') and (not is_admin(str(sender.get('id')),s) or s['users'].get(str(sender.get('id')),{}).get('blocked')):
            security_notice(s,'panel_denied',str(sender.get('id')),'telegram')
    if not sender or sender.get("is_bot") or m.get("chat",{}).get("type")!="private": return True
    uid=str(sender["id"]); raw=str(cb.get("data","") if cb else m.get("text","")).strip()
    has_photo=not cb and bool(m.get("photo"))
    has_document=not cb and bool(m.get("document"))
    has_sticker=not cb and bool(m.get("sticker"))
    has_video=not cb and bool(m.get("video"));has_shared=not cb and isinstance(m.get("chat_shared"),dict)
    if not raw and not has_photo and not has_document and not has_sticker and not has_video and not has_shared: return True
    first=raw.split()[0].split("@")[0].lower() if raw else ""; args=raw.split(maxsplit=1)[1] if " " in raw else ""
    ref=args[4:] if first=="/start" and args.startswith("ref_") else ""
    u=register(s,uid,sender.get("first_name","Member"),ref)
    u.update(last_active=now(),telegram_started=True,telegram_blocked=False)
    u['bot_last_request']={'at':now(),'update_id':update_id,'kind':'callback' if cb else first if first in ('/start','/admin','/stats','/stat','/adminstats','/menu','/support') else 'command' if first.startswith('/') else 'input'}
    panel_attempt=(cb and raw in ('panel','cmd:panel','cmd:planel')) or (not cb and (first in ('/panel','/planel') or first=='/start' and args=='panel'))
    if panel_attempt and (not is_admin(uid,s) or u.get('blocked')):security_notice(s,'panel_denied',uid,'telegram')
    command_button=bool(cb and raw.startswith('cmd:'))
    if command_button:
        command=raw[4:];allowed={c['command'] for c in commands_for(s,uid)}
        raw='/'+command if command in allowed else '';first=raw;args=''
    elif not cb and u.get('flow',{}).get('step')=='command_args' and not raw.startswith('/'):
        if u['flow'].get('t',0)+600>now():
            first='/'+u['flow']['command'];args=raw;raw=first+' '+args;u['flow']={}

    # Honor already-delivered old stop buttons, but expose no subscription commands or controls.
    if cb and raw in ('updates_off','stop_broadcasts'):
        u['updates_on']=False;u['broadcast_hold']=True;cancel_promos(s,uid=uid);audit(s,uid,'updates.opt-out')
        if len(s['outbox'])<1900 and u.get('last_optout_reply',0)+30<=now():
            enqueue(s,uid,md('Broadcasts and optional reminders stopped. Requested replies, invoices and security messages are unaffected.'));u['last_optout_reply']=now()
        return True
    if u.get("blocked"):
        enqueue(s,uid,md("This account is suspended. Contact the administrator.")); return True
    # Flood guard: persist in the same transaction, and do not enqueue one error per spam update.
    if u.get("bot_min")!=now()//60: u["bot_min"]=now()//60; u["bot_count"]=0
    u["bot_count"]+=1
    bot_limit=s['settings']['bot_admin_rpm' if is_admin(uid,s) else 'bot_user_rpm'] if focused_ui(s) else 25
    if u["bot_count"]>bot_limit:
        security_notice(s,'bot_flood',uid,'telegram')
        if focused_ui(s) and u['bot_count']==bot_limit+1:
            key=enqueue(s,uid,md('Too many taps. Wait '+str(60-now()%60)+' seconds, then /start again. Your account is not blocked.'),[[btn('Home','home')]]);nav_job(s,key,uid)
        return True
    if not cb and first=='/start' and not u.get('broadcast_hold'):
        if not u.get('updates_on'):audit(s,uid,'broadcast.auto-enrolled','Real /start; automatic announcement policy available in Help')
        u['updates_on']=True
    action=raw if cb and not command_button else {"/contact":"paysupport","/commands":"commands:0","/freeapi":"starter","/delivery":"delivery","/approvals":"approvals","/forcejoin":"forcejoin","/planel":"panel","/loghere":"loghere","/start":"home","/help":"help","/redeem":"redeem","/createredeem":"createredeem","/revokeredeem":"revokeredeem","/addcredit":"addcredit","/sources":"sources","/addsource":"addsource","/addplan":"addplan","/setvideo":"setvideo","/dashboard":"dashboard","/trial":"trial","/demo":"trial","/menu":"home","/apis":"apis","/create":"create","/buyapi":"create","/referral":"refs","/panel":"panel","/admin":"admin","/adminapis":"adminapis","/adminhelp":"adminhelp","/backup":"backup","/cancel":"home","/id":"id","/stats":"mystats","/daily":"mystats","/adminstats":"adminstats","/verify":"verifyjoin","/operations":"operations","/setmessage":"setmessage","/setwelcomemd":"setwelcomemd","/setcampaign":"setcampaign","/setbuttonemoji":"setbuttonemoji","/confirm":"confirm","/wallet":"wallet","/buy":"buy","/developer":"developer","/paysupport":"paysupport","/terms":"terms","/broadcast":"broadcast","/logs":"testlogs","/setwelcome":"setwelcome","/setsticker":"setsticker","/removesticker":"removesticker","/botstyle":"botstyle"}.get(first,"")
    if first=="/start" and args in ("panel","confirm","trial","demo"): action=args
    if focused_ui(s):
        if first in ('/stats','/stat') and is_admin(uid,s):action='adminstats'
        if first=='/stat' and not is_admin(uid,s):action='mystats'
        if first=='/support':action='supportinbox' if uid in SUPER_IDS else 'paysupport'
        if action=='buy' and not simple_ui(s):action='ownerbuy'
    if focused_ui(s) and not cb and first in ('/start','/admin','/menu') and action in ('home','admin'):recover_bot_screen(s,uid)
    if action=='home':u['bot_view']='home'
    if simple_ui(s) and first in ('/support','/contact'):action='support_removed'
    if first=="/start":queue_commands(s,uid)
    rows=[[btn("Home","home")]]; text=""
    checkpoint=copy.deepcopy(s)
    try:
        if not is_admin(uid,s) and not joined(s,uid) and action not in (('id','help','verifyjoin','paysupport','contacthelp') if focused_ui(s) else ('id','help','verifyjoin')):
            text,rows=join_menu(s)
            if first=='/start':
                welcome_enqueue(s,uid,keyboard=rows);return True
            key=enqueue(s,uid,text,rows,kind='photo' if s['settings']['welcome_photo'] else 'message')
            s['outbox'][key]['priority']=-1
            if s['settings']['welcome_photo']:s['outbox'][key]['photo']=s['settings']['welcome_photo']
            return True
        parameter_help={'createredeem':'COINS USES DAYS, for example: 50 1 7','revokeredeem':'The redeem record ID from Rewards & credits','addcredit':'USER_ID COINS UNIQUE_REFERENCE','addplan':'SOURCE_ID Name | COINS | DAYS | DAILY | RPM | TOTAL','setcampaign':'An existing campaign ID from the admin page'}
        if focused_ui(s) and u.get('flow',{}).get('step')=='support_chat' and (cb or raw.startswith('/')) and not action.startswith(('support','paysupport','contacthelp','contactbuy','owner')):u['flow']={}
        simple_result=simple_customer_action(s,uid,action,raw,cb)
        handled_support=focused_support_action(s,uid,action,raw,cb) if focused_ui(s) and not simple_ui(s) else None
        if simple_result is not None:
            text,rows=simple_result
        elif handled_support is not None:
            text,rows=handled_support;u['bot_view']='support' if u.get('flow',{}).get('step')=='support_chat' else 'supportinbox' if uid in SUPER_IDS and action.startswith(('support','paysupport')) else action.split(':')[0]
        elif command_button and action in parameter_help:
            actor(s,uid,admin=True);u['flow']={'step':'command_args','command':action,'t':now()}
            text=md('Send '+parameter_help[action]+'. Cancel returns to the menu.');rows=[[btn('Cancel','commands:0')]]
        elif action.startswith('commands:'):
            if focused_ui(s):actor(s,uid,admin=True)
            page=action.split(':',1)[1];require(page.isdigit(),'Invalid page.')
            u['flow']={};text,rows=command_buttons(s,uid,int(page))
        elif focused_ui(s) and action.startswith('deliverydefault:'):
            require(uid in SUPER_IDS,'Configured owner only.',403);mode=action.split(':')[1];require(mode in ('txt','text'),'Invalid format.')
            u['flow']={'step':'delivery_default','mode':mode,'t':now()};text=md('Set all customer credential delivery to '+mode+'? Existing API keys are unchanged.');rows=[[btn('Confirm default','deliverydefaultconfirm','success'),btn('Cancel','delivery')]]
        elif focused_ui(s) and action=='deliverydefaultconfirm':
            require(uid in SUPER_IDS,'Configured owner only.',403);f=u.get('flow',{});require(f.get('step')=='delivery_default' and f['t']+600>now(),'Confirmation expired.')
            s['settings'].update(api_receipts_txt=f['mode']=='txt',safe_chat_receipts=True);u['flow']={};audit(s,uid,'credentials.delivery-default')
            text=md('Customer default saved. Existing keys and clients are unchanged.');rows=[[btn('Delivery settings','delivery'),btn('Admin','admin')]]
        elif action=='delivery' or action.startswith('receiptmode:'):
            if focused_ui(s):actor(s,uid,admin=True)
            if action.startswith('receiptmode:'):
                mode=action.split(':',1)[1];require(mode in ('txt','text','default'),'Invalid delivery format.');u['receipt_mode']=mode
            text=md('Credential delivery: '+credential_delivery_mode(s,uid)+'\nTXT is a secret attachment. Text uses non-clickable host/path and header instructions, not a keyed chat URL. Existing keys are not rotated by changing this preference.')
            rows=[[btn('Private TXT','receiptmode:txt'),btn('Safe chat text','receiptmode:text')],[btn('Use owner default','receiptmode:default'),btn('Home','home')]]
            if s['settings'].get('chat_keyed_receipts'):text=md('Credential delivery: '+credential_delivery_mode(s,uid)+'\nChat includes a Ready JSON URL for query-enabled APIs. Link previews are disabled. Existing header-only APIs keep their protection. Existing keys are not rotated by changing delivery.')
            if focused_ui(s):
                text+='\n'+md('Above: your admin receipt preference. Customers use the platform default: '+('TXT' if s['settings']['api_receipts_txt'] else 'safe text')+'.')
                if uid in SUPER_IDS:rows.insert(0,[btn('Customers: TXT','deliverydefault:txt'),btn('Customers: text','deliverydefault:text')])
        elif action=='starter':
            u['flow']={};text,rows=starter_menu(s,uid)
        elif action.startswith('starterpick:'):
            cid=action.split(':',1)[1];src=s['catalog'].get(cid);require(src and src.get('enabled') and src.get('starter_enabled'),'Starter source unavailable.')
            u['flow']={'step':'starter_confirm','draft':{'catalog_id':cid,'quote':starter_policy(s)},'t':now()}
            text=md('Claim '+src['name']+' free? '+str(s['settings']['starter_days'])+' days, '+str(s['settings']['starter_daily'])+'/day. One claim per account. Starts now; separate from the short demo.')
            rows=[[btn('Claim free API','starterconfirm','success'),btn('Cancel','starter')]]
        elif action=='starterconfirm':
            f=u.get('flow',{});require(f.get('step')=='starter_confirm' and f.get('t',0)+300>now(),'Select a starter source again.')
            result=create_starter(s,uid,f['draft']);u['flow']={};enqueue_api_receipt(s,uid,result,'Free starter activated');return True
        elif action.startswith('upgrades:'):
            aid=action.split(':',1)[1];a=owned(s,uid,aid);require(a['owner']==uid and not a.get('is_trial'),'Select your starter or paid API.')
            text=md('Use referral coins for upgrades. Current balance: '+str(u['coins'])+' coins. Upgrades never reset usage; custom keys replace the old key only after confirmation.')
            rows=[]
            if a.get('is_starter'):
                for kind,label in [('extend','Extra days'),('quota','Extra daily quota')]:
                    q=upgrade_quote(s,kind);rows.append([btn(label+' +'+str(q['amount'])+' · '+str(q['price'])+' coins','upgradepick:'+aid+':'+kind)])
            rows.append([btn('Droidx custom key · '+str(s['settings']['custom_key_price'])+' coins','upgradepick:'+aid+':customkey')]);rows.append([btn('Earn coins','refs'),btn('Back','api:'+aid)])
        elif action.startswith('upgradepick:'):
            _,aid,kind=action.split(':',2);a=owned(s,uid,aid);require(a['owner']==uid,'Use your own API.')
            draft={'kind':kind,'quote':upgrade_quote(s,kind)};u['flow']={'step':'custom_key_label' if kind=='customkey' else 'upgrade_confirm','aid':aid,'draft':draft,'t':now()}
            text=md('Send a 1–16 character key label, starting with a letter. Your new key will be Droidx + label + a long random secret; it will not be a guessable name.' if kind=='customkey' else 'Confirm upgrade for '+str(draft['quote']['price'])+' coins?')
            rows=[[btn('Cancel','upgrades:'+aid)]] if kind=='customkey' else [[btn('Confirm upgrade','upgradeconfirm','success'),btn('Cancel','upgrades:'+aid)]]
        elif not cb and u.get('flow',{}).get('step')=='custom_key_label' and not first.startswith('/'):
            f=u['flow'];require(f['t']+600>now(),'Customization expired.');require(re.fullmatch(r'[A-Za-z][A-Za-z0-9_]{0,15}',raw),'Use 1–16 letters/digits/underscore, starting with a letter.')
            f['draft']['label']=raw;f['step']='upgrade_confirm'
            text=md('Customize as Droidx'+raw+' + secure random secret for '+str(f['draft']['quote']['price'])+' coins? Your old key will stop working.')
            rows=[[btn('Pay & customize','upgradeconfirm','success'),btn('Cancel','upgrades:'+f['aid'])]]
        elif action=='upgradeconfirm':
            f=u.get('flow',{});require(f.get('step')=='upgrade_confirm' and f.get('t',0)+600>now(),'Upgrade confirmation expired.')
            r=upgrade_api(s,uid,f['aid'],f['draft']);aid=f['aid'];u['flow']={}
            if r.get('key'):enqueue_api_receipt(s,uid,r,'Customized API key');return True
            text=md(r['message']);rows=[[btn('Manage API','api:'+aid),btn('Home','home')]]
        elif action=='approvals':
            require(uid in SUPER_IDS,'Only the configured owner can review approvals.',403);prune_approvals(s)
            pending=[a for a in s['approvals'].values() if a['status']=='pending']
            text=md('Pending sensitive actions: '+str(len(pending))+'\nNormal API calls and paid purchases do not wait for approval.')
            rows=[[btn(a['scope'][:24]+' · '+a['uid'],'review:'+a['id'])] for a in pending[:20]]+[[btn('Refresh','approvals'),btn('Admin','admin')]]
        elif action.startswith('review:'):
            require(uid in SUPER_IDS,'Owner only.',403);a=s['approvals'].get(action.split(':',1)[1]);require(a and a['status']=='pending','No longer pending.')
            text=md('Requester: '+a['uid']+'\n'+a['summary']);rows=[[btn('Approve','approve:'+a['id'],'success'),btn('Reject','reject:'+a['id'],'danger')],[btn('Back','approvals')]]
        elif action.startswith(('approve:','reject:')):
            op,key=action.split(':',1);text=md(decide_approval(s,uid,key,op=='approve'));rows=[[btn('Other approvals','approvals'),btn('Admin','admin')]]
        elif action=='loghere':
            actor(s,uid,superonly=True);text=md('Send /loghere inside your intended private logs group. The bot must be admin there. This command does not select a group from DM.')
        elif action=='forcejoin':
            actor(s,uid,superonly=True);u['flow']={}
            text=md('Required joins: select a group/channel you administer. The bot must also be admin. Private groups need a working invite link. Private logs stay separate.')
            rows=[[btn('Select group','joinpick:group'),btn('Select channel','joinpick:channel')]]+[[btn('Remove '+c['title'],'joinremove:'+c['chat_id'],'danger')] for c in s['settings']['force_join_channels']]+[[btn('Admin','admin')]]
        elif action.startswith('joinpick:'):
            channel=action.split(':',1)[1];require(channel in ('group','channel'),'Invalid picker.');queue_join_picker(s,uid,channel=='channel');return True
        elif has_shared:
            actor(s,uid,superonly=True);f=u.get('flow',{});shared=m['chat_shared']
            require(f.get('step')=='join_pick' and f.get('request_id')==shared.get('request_id') and f.get('t',0)+600>now(),'Selection expired. Use Force join → Select again.')
            target=str(shared.get('chat_id',''));require(re.fullmatch(r'-[1-9][0-9]{4,19}',target),'Invalid Telegram chat ID.')
            k=enqueue(s,uid,'',kind='joinsetup');s['outbox'][k].update(target=target,channel=f['channel'],request_id=f['request_id'],expires=now()+300,priority=-10)
            f['step']='join_probe';return True
        elif not cb and u.get('flow',{}).get('step')=='join_link' and not first.startswith('/'):
            actor(s,uid,superonly=True);f=u['flow'];require(f['t']+600>now(),'Selection expired.');f['draft']['url']=raw
            require(re.fullmatch(r'https://t\.me/[A-Za-z0-9_+/-]{3,150}',raw),'Send a working HTTPS t.me invite link.')
            f['step']='join_confirm';text=md('Add required join: '+f['draft']['title']+'?');rows=[[btn('Confirm','joinconfirm','success'),btn('Cancel','forcejoin')]]
        elif action=='joinconfirm':
            actor(s,uid,superonly=True);f=u.get('flow',{});require(f.get('step')=='join_confirm' and f.get('t',0)+600>now(),'Selection expired.')
            channels=s['settings']['force_join_channels']+[f['draft']];ops_settings(s,uid,{'force_join_channels':channels});u['flow']={}
            text=md('Required join saved. New activations/API creations must verify it.');rows=[[btn('Manage joins','forcejoin'),btn('Admin','admin')]]
        elif action.startswith('joinremove:'):
            actor(s,uid,superonly=True);cid=action.split(':',1)[1];u['flow']={'step':'join_remove','id':cid,'t':now()}
            text=md('Remove this required join: '+cid+'?');rows=[[btn('Confirm removal','joinremoveconfirm','danger'),btn('Cancel','forcejoin')]]
        elif action=='joinremoveconfirm':
            actor(s,uid,superonly=True);f=u.get('flow',{});require(f.get('step')=='join_remove' and f['t']+300>now(),'Confirmation expired.')
            ops_settings(s,uid,{'force_join_channels':[c for c in s['settings']['force_join_channels'] if c['chat_id']!=f['id']]});u['flow']={};text=md('Required join removed.');rows=[[btn('Manage joins','forcejoin')]]
        elif action=='redeem':
            if args:
                r=claim_redeem(s,uid,args);u['flow']={};text=md(f"🎁 Redeemed {r['coins']} coins. Balance: {r['balance']}.");rows=[[btn('Buy API','create','success'),btn('Wallet','wallet')]]
            else:u['flow']={'step':'redeem','t':now()};text=md('Send your redeem code within five minutes. One claim per account. /cancel exits.')
        elif not cb and u.get('flow',{}).get('step')=='redeem' and not first.startswith('/'):
            require(u['flow']['t']+300>now(),'Redeem prompt expired. Use /redeem again.');r=claim_redeem(s,uid,raw);u['flow']={}
            text=md(f"🎁 Added {r['coins']} coins. Balance: {r['balance']}.");rows=[[btn('Buy API','create','success'),btn('Wallet','wallet')]]
        elif action=='createredeem':
            actor(s,uid,superonly=True);parts=args.split();require(len(parts)==3,'Use /createredeem COINS MAX_USERS DAYS. Example: /createredeem 50 10 7')
            r=create_redeem(s,uid,{k:command_number(v,k) for k,v in zip(('coins','uses','days'),parts)})
            text='*Redeem code created*\n'+code(r['code'])+'\n'+md(f"{r['coins']} coins · {r['uses']} users · expires {iso(r['expires'])}\nRecord: {r['id']}\nSave the code; only its hash remains after delivery. Do not publish unintentionally.")
            rows=[[{'text':'Copy code','copy_text':{'text':r['code']}}],[btn('Admin','admin')]]
        elif action=='revokeredeem':
            actor(s,uid,superonly=True);require(bool(args),'Use /revokeredeem RECORD_ID (shown when creating the code).')
            text=md(admin_action(s,uid,'redeem',{'revoke':True,'id':args})['message'])
        elif action=='addcredit':
            actor(s,uid,superonly=True);parts=args.split();require(len(parts)==3,'Use /addcredit USER_ID COINS UNIQUE_REFERENCE. Example: /addcredit 123456789 50 bonus_oct01')
            amount=command_number(parts[1],'Coins',1,1000000);require(parts[0] in s['users'],'User must /start first.')
            require(bool(re.fullmatch(r'[A-Za-z0-9_-]{6,64}',parts[2])),'Reference: 6–64 letters/digits/dash/underscore.')
            u['flow']={'step':'credit_confirm','t':now(),'draft':{'uid':parts[0],'coins':amount,'reference':parts[2]}}
            text=md(f'Add {amount} coins to {parts[0]}? Reference: {parts[2]}. Repeating this reference cannot credit twice.')
            rows=[[btn('Confirm credit','creditconfirm','success'),btn('Cancel','home')]]
        elif action=='creditconfirm':
            actor(s,uid,superonly=True);f=u.get('flow',{});require(f.get('step')=='credit_confirm' and f['t']+300>now(),'Credit confirmation expired.')
            r=grant_credit(s,uid,f['draft']);u['flow']={};text=md(r['message'])
        elif action=='adminapis' or action.startswith('adminapis:'):
            actor(s,uid,admin=True);page=int(action.split(':',1)[1]) if ':' in action else 0;require(0<=page<=100,'Invalid page.')
            entries=sorted(s['apis'].values(),key=lambda a:a['created'],reverse=True);part=entries[page*8:(page+1)*8]
            text='*Admin · All APIs*\n'+md(f'{len(entries)} endpoints · page {page+1}. Select an endpoint. Shared provider settings are edited in API catalogue, not inside a purchased endpoint.')
            rows=[[btn(a['name'][:38]+' · '+a['owner'][:16],'api:'+a['id'])] for a in part]
            navigation=[]
            if page:navigation.append(btn('Previous','adminapis:'+str(page-1)))
            if (page+1)*8<len(entries):navigation.append(btn('Next','adminapis:'+str(page+1)))
            if navigation:rows.append(navigation)
            rows.append([btn('Admin','admin')])
        elif action.startswith('apilimits:'):
            actor(s,uid,admin=True);aid=action.split(':',1)[1];a=owned(s,uid,aid);require(not a.get('is_trial'),'Trial limits cannot be edited.')
            u['flow']={'step':'admin_api_limits','t':now(),'aid':aid}
            text=md('Send DAILY RPM EXTEND_DAYS HEADER_ONLY. Example: 100 30 0 yes. yes requires X-API-Key/Bearer headers and disables public access. no retains keyed-URL compatibility. Existing usage is never reset. /cancel exits.')
        elif not cb and u.get('flow',{}).get('step')=='admin_api_limits' and not first.startswith('/'):
            actor(s,uid,admin=True);f=u['flow'];require(f['t']+300>now(),'Edit prompt expired.');parts=raw.split();require(len(parts)==4 and parts[3].lower() in ('yes','no'),'Use DAILY RPM EXTEND_DAYS yes/no.')
            d={'daily':command_number(parts[0],'Daily',1,100000),'rpm':command_number(parts[1],'RPM',1,1000),'extend_days':command_number(parts[2],'Extra days',0,365),'header_only':parts[3].lower()=='yes'}
            f.update(step='admin_api_confirm',draft=d);text=md(f"Save {d['daily']}/day, {d['rpm']}/minute, +{d['extend_days']} days, header-only {d['header_only']}?")
            rows=[[btn('Save endpoint','adminapiconfirm','success'),btn('Cancel','adminapis')]]
        elif action=='adminapiconfirm':
            actor(s,uid,admin=True);f=u.get('flow',{});require(f.get('step')=='admin_api_confirm' and f['t']+300>now(),'Confirmation expired.')
            if s['settings'].get('owner_approval_required') and uid not in SUPER_IDS:
                new_approval(s,uid,'api_limits',{'id':f['aid'],**f['draft']},kind='bot');u['flow']={}
                enqueue(s,uid,md('Endpoint change sent to the owner for approval.'),[[btn('Admin APIs','adminapis')]]);return True
            r=api_action(s,uid,f['aid'],'edit',f['draft']);u['flow']={};text=md('Endpoint settings saved. Existing usage and purchased plan contract were not erased.');rows=[[btn('Admin APIs','adminapis')]]
        elif action=='sources':
            actor(s,uid,admin=True)
            text='*Source IDs*\n'+md('\n'.join(c['id']+' — '+c['name']+' ('+str(len(c.get('plans',[])))+' plans)' for c in list(s['catalog'].values())[:25]) or 'No sources yet. Use /addsource.')
            rows=[[btn('Add source','addsource','success'),btn('Admin','admin')]]
        elif action=='addsource':
            actor(s,uid,admin=True);u['flow']={'step':'source_name','t':now(),'draft':{}};text=md('Send a short source/category name. This publishes a customer source, not a personal endpoint. /cancel exits.')
        elif action=='sourceconfirm':
            actor(s,uid,admin=True);f=u.get('flow',{});require(f.get('step')=='source_confirm' and f.get('t',0)+900>now(),'Source confirmation expired.')
            if s['settings'].get('owner_approval_required') and uid not in SUPER_IDS:
                new_approval(s,uid,'catalog',f['draft'],kind='bot');u['flow']={}
                enqueue(s,uid,md('Source draft sent to the owner for approval.'),[[btn('Admin','admin')]]);return True
            r=admin_action(s,uid,'catalog',f['draft']);u['flow']={};text=md('Source saved: '+r['id']+'\nUse /addplan '+r['id']+' Starter | 250 | 10 | 100 | 30 | 0\nFields: name | coins | days | daily | RPM | total (0 = no total cap).')
        elif action=='addplan':
            actor(s,uid,admin=True);parts=args.split(maxsplit=1);require(len(parts)==2,'Use /addplan SOURCE_ID Name | COINS | DAYS | DAILY | RPM | TOTAL. Get IDs with /sources.')
            cid,rest=parts;source=s['catalog'].get(cid);require(source,'Source not found. Use /sources.')
            fields=[x.strip() for x in rest.split('|')];require(len(fields)==6,'Use six fields: name | coins | days | daily | RPM | total (0 = no total cap).')
            item=dict(zip(('name','price','days','daily','rpm','total'),fields));item.update({k:command_number(item[k],k,0,100000000) for k in ('price','days','daily','rpm','total')});item['id']='p_'+secrets.token_hex(4)
            plans=validate_source_plans(source.get('plans',[])+[item])
            if s['settings'].get('owner_approval_required') and uid not in SUPER_IDS:
                new_approval(s,uid,'plan',{'id':cid,'plan':plans[-1]},kind='bot')
                enqueue(s,uid,md('Plan draft sent to the owner for approval.'),[[btn('Admin','admin')]]);return True
            source['plans']=plans;check_data_capacity(s);audit(s,uid,'catalog.plan.add',cid)
            text=md('Plan saved: '+plans[-1]['name']+'\n'+plan_summary(plans[-1])+'\nCustomers now choose a plan before buying. Edit/disable plans in the admin page.')
        elif not cb and u.get('flow',{}).get('step','').startswith('source_') and not first.startswith('/'):
            text,rows=source_wizard(s,uid,raw)
        elif action=='dashboard':
            actor(s,uid,admin=True);s['settings'].update(welcome_dashboard=True,welcome_sticker='',welcome_sticker_info={});clear_welcome_stickers(s);u['flow']={}
            audit(s,uid,'welcome.dashboard');text=md('Dynamic dashboard enabled; separate welcome sticker removed. /start previews it.')
        elif action=='setvideo':
            actor(s,uid,admin=True);u['flow']={'step':'welcome_video','t':now()};text=md('Send the original Telegram video (up to 20 MB) within ten minutes. A screenshot cannot supply the video. /cancel exits.')
        elif has_video:text=md(save_welcome_video(s,uid,m))
        elif action=='verifyjoin':
            text=md(request_join(s,uid));rows=[[btn('Home','home')]]
        elif action in ('trial','demo'):
            u['flow']={};text,rows=trial_menu(s,uid)
        elif action.startswith('trialpick:'):
            cid=action.split(':',1)[1];src=s['catalog'].get(cid)
            require(src and src.get('enabled') and src.get('trial_enabled'),'Trial source unavailable.')
            require(uid not in s['trial_claims'],'Your one-time trial is already used.',409,'TRIAL_USED')
            q=trial_policy(s['settings']);u['flow']={'step':'trial_confirm','t':now(),'draft':{'catalog_id':cid,'quote':q}}
            text='*Confirm free trial*\n'+md(src['name']+f"\n{q['minutes']} minutes · {q['requests']} total requests · {q['rpm']}/minute\nThe clock starts NOW when you confirm. No coins deducted. One trial total per account, not per source. Pausing does not stop the clock.")
            rows=[[btn('Start my trial','trialconfirm','success'),btn('Cancel','home')]]
        elif action=='trialconfirm':
            f=u.get('flow',{});require(f.get('step')=='trial_confirm' and f.get('t',0)+300>now(),'Trial confirmation expired. Use /trial again.')
            result=create_trial(s,uid,f['draft']);u['flow']={}
            text='*⏱ Trial started*\n'+md(result['name']+'\nExpires: '+iso(result['expires'])+f"\nTotal request budget: {result['trial_limit']}")+'\n\n*Ready JSON URL*\n'+code(result['ready_url'])+'\n\n'+md('Save this key privately. Trial time/budget never restarts; missed key delivery can be recovered by rotating the key in My APIs before expiry. Paid APIs are separate.')
            if use_safe_receipt(s,uid):
                enqueue_api_receipt(s,uid,result,'Trial started');return True
            rows=ready_url_buttons(result)+[[btn('My APIs','apis'),btn('Developer','developer')]]
        elif action in ('mystats','adminstats'):
            text=stats_message(s,uid,action=='adminstats');rows=[[btn('Refresh stats',action),btn('Home','home')]]
        elif action=='buttonicons':
            actor(s,uid,superonly=True)
            text='*💙 Button custom emoji*\n\n'+md('Choose a button colour, then send ONE custom emoji from Telegram. Ordinary sticker files cannot be embedded in buttons. Telegram bot eligibility is required; rejected decorations retry without custom emoji. IDs can also be edited/cleared in Operations.')
            rows=[[btn('Blue icon','captureicon:primary'),btn('Green icon','captureicon:success','success'),btn('Red icon','captureicon:danger','danger')],[btn('Appearance','botstyle')]]
        elif action=='setbuttonemoji' or action.startswith('captureicon:'):
            actor(s,uid,superonly=True);style=action.split(':',1)[1] if action.startswith('captureicon:') else args or 'all';require(style in ('all','primary','success','danger'),'Use /setbuttonemoji all, primary, success or danger.')
            u['flow']={'step':'buttonemoji','style':style,'draft':{},'t':now()}
            text=md('Send one Telegram custom emoji within 10 minutes. Normal emoji and sticker files do not contain a button custom-emoji ID. Telegram bot eligibility still applies. /cancel aborts.')
        elif not cb and u.get('flow',{}).get('step')=='buttonemoji' and not first.startswith('/'):
            actor(s,uid,superonly=True);f=u['flow'];require(f.get('t',0)+600>now(),'Emoji capture expired.')
            ids=[e.get('custom_emoji_id') for e in m.get('entities',[]) if e.get('type')=='custom_emoji']
            require(len(ids)==1 and isinstance(ids[0],str) and re.fullmatch(r'[0-9]{1,32}',ids[0]),'Send exactly one custom emoji, not a sticker or ordinary emoji.')
            for style in (('primary','success','danger') if f['style']=='all' else (f['style'],)):s['settings']['button_icons'][style]=ids[0]
            u['flow']={};audit(s,uid,'operations.button-emoji')
            text=md('Button emoji saved. /start previews it. If Telegram rejects it, the message retries without custom emoji.')
        elif action=='operations':
            actor(s,uid,superonly=True)
            text='*⚙️ Operations*\n'+md('Open the Operations panel to configure ALL required join channels/groups, a separate private logs channel, heartbeat, quota warnings and custom emoji button IDs. The bot must be admin in every configured channel/group. /setmessage captures formatted welcome text; /setwelcomemd captures Markdown; /setcampaign ID captures campaign text.')
            rows=[[btn('Operations panel','panel'),btn('Verify logs','testlogs','success')],[btn('Admin stats','adminstats'),btn('Home','home')]]
        elif action=='testlogs':
            text=md(queue_log_test(s,uid)['message'])
        elif action=='broadcast':
            actor(s,uid,admin=True);u['flow']={'step':'broadcast_text','draft':{},'t':now()}
            text=md('Send a text broadcast (up to 700 text units). Telegram formatting/custom emoji can be captured. You will preview and confirm before scheduling. Never include keys or private records. /cancel exits.')
        elif not cb and u.get('flow',{}).get('step')=='broadcast_text' and not first.startswith('/'):
            actor(s,uid,admin=True);require(u['flow']['t']+600>now(),'Broadcast draft expired. Use /broadcast.')
            raw_text=m.get('text');require(isinstance(raw_text,str) and 0<text_units(raw_text)<=700,'Send a text message up to 700 text units.')
            entities=rich_entities(raw_text,m.get('entities',[]));formatted_template(raw_text,'entities',entities)
            u['flow']={'step':'broadcast_schedule','draft':{'text':raw_text,'entities':entities},'t':now()}
            key=enqueue(s,uid,raw_text,[[btn('One-time broadcast','broadcastmode:once','success'),btn('Daily broadcast','broadcastmode:random')],[btn('Cancel','home')]])
            attach_rich(s,key,raw_text,'entities',entities,u,header='Preview — only you can see this\n\n',footer='\n\nChoose one-time or daily. Delivery respects the configured window, daily cap and historical exclusions.')
            check_data_capacity(s);return True
        elif not cb and u.get('flow',{}).get('step') in ('broadcast_schedule','broadcast_confirm') and not first.startswith('/'):
            actor(s,uid,admin=True);text=md('Use the schedule/confirmation buttons, or /cancel to discard this draft.')
            rows=[[btn('One-time','broadcastmode:once'),btn('Daily','broadcastmode:random')]] if u['flow']['step']=='broadcast_schedule' else [[btn('Confirm schedule','broadcastconfirm','success'),btn('Cancel','home')]]
        elif action.startswith('broadcastmode:'):
            actor(s,uid,admin=True);f=u.get('flow',{});require(f.get('step')=='broadcast_schedule' and f.get('t',0)+600>now(),'Broadcast draft expired.')
            mode=action.split(':',1)[1];require(mode in ('once','random'),'Invalid broadcast schedule.')
            f['draft']['trigger']=mode;f['step']='broadcast_confirm'
            text=md(('Schedule one-time broadcast?' if mode=='once' else 'Schedule daily broadcast, every 24 hours?')+'\nNo messages have been sent. Quiet hours, per-user caps and the external scheduler apply.'+('\nYour confirmation will enable the campaign master switch.' if role(uid,s)=='superadmin' and not s['settings']['campaigns_enabled'] else '\nThe owner must enable the campaign master switch.' if not s['settings']['campaigns_enabled'] else ''))
            rows=[[btn('Confirm schedule','broadcastconfirm','success'),btn('Cancel','home')]]
        elif action=='broadcastconfirm':
            actor(s,uid,admin=True);f=u.get('flow',{});require(f.get('step')=='broadcast_confirm' and f.get('t',0)+600>now(),'Broadcast confirmation expired.')
            draft=f['draft'];formatted_template(draft['text'],'entities',draft['entities'])
            if s['settings'].get('owner_approval_required') and uid not in SUPER_IDS:
                key,_=new_approval(s,uid,'broadcast',draft,kind='bot');u['flow']={}
                enqueue(s,uid,md('Broadcast draft sent to the configured owner for approval. No campaign has been activated.'),[[btn('Admin','admin')]]);return True
            result=save_campaign(s,uid,{'name':'Bot broadcast '+str(now()),'text':draft['text'],'trigger':draft['trigger'],'min_hours':24,'max_hours':24,'enabled':True})
            campaign=s['campaigns'][result['id']];campaign.update(text=draft['text'],text_mode='entities',text_entities=draft['entities'])
            if role(uid,s)=='superadmin':s['settings']['campaigns_enabled']=True
            u['flow']={};check_data_capacity(s)
            ops_log(s,'broadcast.scheduled',uid,result['id']+' · '+('one-time' if draft['trigger']=='once' else 'daily'))
            text=md('Broadcast saved: '+result['id']+'\n'+('One-time schedule.' if draft['trigger']=='once' else 'Daily schedule, every 24 hours.')+'\n'+('Waiting for the eligible delivery window and authenticated scheduler. This is not a sent/delivered confirmation.' if s['settings']['campaigns_enabled'] else 'Waiting for the owner to enable the campaign master switch, then the scheduler.'))
            rows=[[btn('Admin controls','admin'),btn('Home','home')]]
        elif action in ('setmessage','setwelcomemd','setcampaign'):
            actor(s,uid,admin=True)
            if action=='setcampaign':require(args in s['campaigns'],'Use /setcampaign followed by an existing campaign ID from the panel.')
            u['flow']={'step':'welcome_md' if action=='setwelcomemd' else 'rich_message','campaign':args if action=='setcampaign' else '', 'draft':{},'t':now()}
            text=md('Send your Markdown text within 10 minutes. Supported: *bold*, _italic_, __underline__, ~strike~, ||spoiler||, `code`, and [label](https://link). /cancel aborts.' if action=='setwelcomemd' else 'Send a Telegram-formatted text message (or photo caption) within 10 minutes. Bold/italic/links/custom emoji are captured. No image is changed. /cancel aborts.')
        elif not cb and u.get('flow',{}).get('step') in ('rich_message','welcome_md') and not first.startswith('/'):
            text=md(capture_message(s,uid,m,u['flow']))
        elif has_sticker:
            text=md(save_welcome_sticker(s,uid,m));rows=[[btn('Bot appearance','botstyle'),btn('Preview welcome','previewwelcome')]]
        elif has_photo:
            text=md(save_welcome_photo(s,uid,m));rows=[[btn('Home','home')]]
        elif action=='setsticker':
            actor(s,uid,admin=True);u['flow']={'step':'welcome_sticker','draft':{},'t':now()}
            text=md('Send your selected sticker in this private chat within 10 minutes. Static, animated and video regular stickers are supported, including premium regular sticker file IDs accepted by Telegram. Send it as a sticker, not as a file or custom emoji. /cancel aborts.')
        elif action=='removesticker':
            actor(s,uid,admin=True);clear_welcome_stickers(s)
            s['settings'].update(welcome_sticker='',welcome_sticker_info={});u['flow']={}
            audit(s,uid,'welcome.sticker.remove');text=md('Welcome sticker removed. Photo and text are unchanged. An already in-flight sticker may still arrive.')
            rows=[[btn('Bot appearance','botstyle')]]
        elif action=='botstyle' or action.startswith('style:'):
            actor(s,uid,admin=True)
            if action.startswith('style:'):
                style=action.split(':',1)[1];require(style in ('compact','classic'),'Unknown text style.')
                s['settings']['bot_text_style']=style;audit(s,uid,'bot.style',style)
            text,rows=bot_design(s,uid)
        elif action=='previewwelcome':
            actor(s,uid,admin=True)
            require(u.get('last_design_preview',0)+30<=now(),'Wait 30 seconds between previews.',429)
            u['last_design_preview']=now();welcome_enqueue(s,uid,preview=True);return True
        elif action=='setwelcome':
            actor(s,uid,admin=True);u['flow']={'step':'welcome_photo','draft':{},'t':now()}
            text=md('Send the welcome image as a photo (not a file) in this private chat within 10 minutes. Its optional caption will replace the welcome message. /cancel aborts. Then use /start to see the photo welcome.')
        elif first=='/start' and action=='home':
            u['flow']={};welcome_enqueue(s,uid);return True
        elif action=="help":
            u['flow']={};text,rows=user_help(s,uid)
        elif action=="adminhelp":
            text,rows=admin_help(s,uid)
        elif action=="home":
            u["flow"]={};text,rows=menu(s,uid)
        elif action in ('wallet','buy'):
            st=s['settings'];text=bot_title(s,"Wallet")+"\n\n"+md(f"{u['coins']} coins · {u['diamonds']} diamonds\n1 approved referral = {st['referral_reward']} coins\nDiamond → coin rate: {st['diamond_coin_rate'] or 'not configured'}\nAPI currency and price are set per catalogue source.")
            if u.get('wallet_hold'):text+='\n'+md('Wallet hold: resolve your negative balance with support.')
            text+='\n\n'+md('Buy using Telegram Stars. Stars are the payment currency, not your app diamonds. Read /terms before paying. /paysupport for assistance.')
            rows=[[btn(f"{p['name']}: {p['amount']} {p['currency']} · {p['stars']} Stars",'buy:'+p['id'],'success')] for p in st['purchase_packs'] if p['enabled']]
            if st['diamond_coin_rate']>0:rows.append([btn('Convert diamonds','convert')])
            rows.append([btn('Home','home')])
        elif action.startswith('buy:'):
            result=new_order(s,uid,action.split(':',1)[1]);text=md(result['message'])
        elif action=='convert':
            require(s['settings']['diamond_coin_rate']>0,'Conversion is not configured.')
            u['flow']={'step':'convert_amount','draft':{},'rate':s['settings']['diamond_coin_rate'],'t':now()}
            text=md(f"1 diamond = {s['settings']['diamond_coin_rate']} coins. Send the whole number of diamonds to convert. Conversion is one-way.")
        elif action=='convertconfirm':
            f=u.get('flow',{});require(f.get('step')=='convert_confirm' and f.get('t',0)+1800>now(),'Conversion expired. Start again.')
            result=convert_diamonds(s,uid,f['draft']['amount'],f['rate']);u['flow']={};text=md(result['message'])
        elif action=='developer':
            st=s['settings'];text=bot_title(s,'Developer')+'\n\n'+md(st['developer_name'])+'\n'+md(st['developer_about'])
            if st.get('developer_username'):text+='\n'+md('@'+st['developer_username'])
            if st['developer_website']:text+='\n'+md(st['developer_website'])
            text+='\n\n'+md('Every source has its own query name and saved example. Use /demo for your one-time trial, /create for paid APIs and /apis for usage, edits and key rotation. Your full keyed URL is delivered here in the bot. Keep it private. Only use authorized sources and safe test data.')
            rows=[[btn('Free trial API','trial','success'),btn('My APIs','apis')],[btn('Payment support','paysupport')]]
            if is_admin(uid,s):rows.append([btn('Admin panel','panel')])
            if st.get('developer_username'):rows.insert(0,[btn('💙 Contact developer',url='https://t.me/'+st['developer_username'])])
        elif action=='paysupport':
            name=s['settings']['support_username'];text=md('Purchase/payment support: '+('@'+name if name else 'Request the owner below without needing a public username.')+' Never send passwords, API keys or private records.')
            rows=[[btn('Ask about buying','contactbuy'),btn('Payment help','contacthelp')]]
            if name:rows.append([btn('DM owner support',url='https://t.me/'+name)])
            rows.append([btn('Wallet','wallet'),btn('Home','home')])
        elif action in ('contactbuy','contacthelp'):
            require(u.get('support_requested_at',0)+900<=now(),'An owner contact request was already sent. Please wait 15 minutes before another request.',429)
            require(SUPER_IDS,'Owner contact is not configured. Use the saved support username.',503)
            u['support_requested_at']=now()
            for owner in sorted(SUPER_IDS):
                soft_message(s,owner,'*Customer contact request*\n'+md(('Purchase inquiry' if action=='contactbuy' else 'Payment/support help')+'\nAccount: '+uid),[[btn('Reply through bot','supportreply:'+uid),btn('Open customer profile',url='tg://user?id='+uid)]])
            text=md('Your contact request was sent to the owner queue. The owner can reply through this bot. This does not purchase an API or deduct coins.');rows=[[btn('Browse plans','create'),btn('Home','home')]]
        elif action.startswith('supportreply:'):
            require(uid in SUPER_IDS,'Configured owner only.',403);target=action.split(':',1)[1]
            require(target.isdigit() and target in s['users'],'Customer unavailable.')
            u['flow']={'step':'support_reply','target':target,'t':now()};text=md('Send your reply for account '+target+' within 10 minutes. Do not send passwords, API keys or private records.');rows=[[btn('Cancel','admin')]]
        elif not cb and u.get('flow',{}).get('step')=='support_reply' and not first.startswith('/'):
            require(uid in SUPER_IDS,'Configured owner only.',403);f=u['flow'];require(f['t']+600>now() and 1<=text_units(raw)<=800,'Reply must be 1–800 units and within 10 minutes.')
            target=f['target'];require(not s['users'].get(target,{}).get('blocked',True),'Customer unavailable.')
            soft_message(s,target,'*Owner reply*\n'+md(raw),[[btn('Owner contact','paysupport'),btn('Home','home')]])
            u['flow']={};text=md('Owner reply queued for the customer.');rows=[[btn('Admin','admin')]]
        elif action=='terms':text=md(s['settings']['payment_terms'])
        elif action=="id": text="Your Telegram ID: "+code(uid)
        elif action=="activate": text=md(activate(s,uid)); rows=[[btn("Continue","home","success")]]
        elif action=="refs":
            st=s['settings'];link='https://t.me/'+bot_username(s)+'?start=ref_'+uid
            text='*🎁 Invite and earn*\n\n'+md(f"You earn {st['referral_reward']} coins; your new friend earns {st['referral_new_user_reward']} coins.\nBalance: {u['coins']} coins · Qualified: {u.get('refs',0)}\nJoin ALL required channels/groups and activate. "+('Rewards require admin approval.' if st['referral_approval'] else 'Eligible rewards are credited automatically once.'))
            text+='\n\n'+code(link)+'\n\n'+md('Default API: '+referral_requirement(s,uid))
            for c in list(s['catalog'].values())[:8]:
                if c['enabled']:text+='\n'+md(c['name']+': '+referral_requirement(s,uid,c))
            text+='\n\n'+md('Only genuinely new Telegram accounts entering via your link qualify. Self/existing/repeated referrals do not earn again. Referral estimates are not a reward guarantee.')
            share='https://t.me/share/url?'+urllib.parse.urlencode({'url':link,'text':f"Join SR DARK. Complete required joins and activation to earn {st['referral_new_user_reward']} coins. Explore API plans in the bot."})
            rows=[[btn('💙 Share referral',url=share)],[btn('API catalogue','create'),btn('Wallet','wallet','success')],[btn('Home','home')]]
        elif action=="confirm":
            value=issue_confirmation(s,uid)
            text="*Sensitive action confirmation*\n\n"+code(value)+"\n\n"+md("Only enter this code in your own SR DARK Security centre. Valid for 3 minutes, one use, 5 attempts. Do not share it. If you did not request it, ignore this message.")
            rows=[[btn("Security centre",url=str(cfg("BASE_URL")) or "https://example.com")]]
        elif action=="panel":
            token=issue_login(s,uid)
            text="*Secure panel login*\n\n"+md("Open the panel and paste this one-time code. Expires in 5 minutes; do not share.")+"\n\n"+code(token)
            rows=[[btn("Open web panel",url=str(cfg("BASE_URL")) or "https://example.com")]]
        elif action=='create' or action.startswith('catalogpage:'):
            page=0
            if action.startswith('catalogpage:'):
                value=action.split(':',1)[1];require(bool(re.fullmatch(r'[0-9]{1,6}',value)),'Invalid catalogue page.')
                page=int(value)
            u['flow']={};text,rows=bot_catalogue(s,uid,page)
        elif action=='customcreate':
            require(s['settings']['allow_custom'] or is_admin(uid,s),'Custom APIs are disabled.',403)
            u['flow']={};text=md('Choose a custom API type. Use only sources and data you are authorized to provide.')
            rows=[[btn('Static JSON','newstatic'),btn('Proxy URL','newproxy')],[btn('Back to API catalogue','create')]]
        elif action.startswith('plan:'):
            _,cid,pid=action.split(':',2);src=s['catalog'].get(cid)
            require(src and src.get('enabled'),'Source unavailable.')
            plan=selected_plan(src,pid)
            u['flow']={'step':'confirm','t':now(),'draft':{'catalog_id':cid,'name':src['name'],'plan_id':pid,'quote_plan':plan,'quote_price':plan['price'],'quote_currency':'coins'}}
            text='*Confirm API plan*\n'+md(src['name']+' · '+plan['name']+'\n'+plan_summary(plan)+'\nYour personal key is bound to this source. Expiry starts on purchase. Accepted attempts count, including upstream failures.')
            if is_admin(uid,s):text+='\n'+md('Admin test: no coins charged.')
            rows=[[btn('Demo response','sourcepreview:'+cid)],[btn('Confirm purchase','confirmcreate','success'),btn('Other plans','catalog:'+cid)]]
            if focused_ui(s) and not simple_ui(s):rows.insert(0,[btn('Ask owner · '+str(plan['price'])+' coins','ownerpick:'+cid+':'+pid)])
        elif action.startswith("catalog:"):
            cid=action.split(":",1)[1]; c=s["catalog"].get(cid); require(c and c["enabled"],"Catalogue unavailable.")
            if c.get('plans'):
                u['flow']={};available=[p for p in c['plans'] if p.get('enabled',True)]
                text='*Choose a plan*\n'+md(c['name']+'\n'+'\n'.join(p['name']+': '+plan_summary(p) for p in available))
                rows=[[btn(p['name']+' · '+str(p['price'])+' coins','plan:'+cid+':'+p['id'],'success')] for p in available]+[[btn('Demo response','sourcepreview:'+cid),btn('Back','create')]]
            else:
                u["flow"]={"step":"confirm","draft":{"catalog_id":cid,"name":c["name"],"quote_currency":api_price(s,c)[0],"quote_price":api_price(s,c)[1]},"t":now()}
                currency,price=api_price(s,c);text=md("Create "+c["name"]+f"? Cost: {0 if is_admin(uid,s) else price} {currency}.\n"+referral_requirement(s,uid,c))
                rows=[[btn("🔎 Demo response","sourcepreview:"+cid)],[btn("🛒 Confirm purchase","confirmcreate","success"),btn("Back","create")]]
                if focused_ui(s) and not simple_ui(s):rows.insert(0,[btn('Ask owner · '+str(price)+' '+currency,'ownerpick:'+cid+':default')])
        elif action.startswith('sourcepreview:'):
            cid=action.split(':',1)[1];source=s['catalog'].get(cid);require(source and source.get('enabled'),'Source unavailable.')
            text=md(source['name'])+'\n\n'+source_preview(source)
            rows=[[btn('🛒 Buy this API','catalog:'+cid,'success'),btn('Other APIs','create')],[btn('⏱ Try API','trialpick:'+cid)]] if source.get('trial_enabled') else [[btn('🛒 Buy this API','catalog:'+cid,'success'),btn('Other APIs','create')]]
            draft=u.get('flow',{}).get('draft',{})
            if u.get('flow',{}).get('step')=='confirm' and draft.get('catalog_id')==cid:
                rows.insert(0,[btn('Buy selected plan' if draft.get('plan_id') else 'Confirm purchase','confirmcreate','success')])
        elif action in ("newstatic","newproxy"):
            u["flow"]={"step":"name","draft":{"mode":"static" if action=="newstatic" else "proxy"},"t":now()}
            text=md("Send an API name (1–60 characters).")
        elif action=="confirmcreate":
            f=u.get("flow",{}); require(f.get("step")=="confirm" and f.get("t",0)+1800>now(),"Wizard expired. Start again.")
            draft=copy.deepcopy(f["draft"])
            r=api_action(s,uid,f["edit"],"edit",draft) if f.get("edit") else create_api(s,uid,draft)
            u["flow"]={}
            if r.get("key"):
                text="*API created*\n\n"+md(r["name"])+"\nEndpoint: "+code(r["endpoint"])+"\nKey: "+code(r["key"])+"\n\n*Ready URL*\n"+code(r["ready_url"])+"\n\n"+md("Save privately. The URL contains your secret key. Your saved example input is already filled in. Change the query value when needed. Header authentication is safer. Use Rotate if lost.")
            else: text=md("API saved.")
            if r.get("plan"):text+='\n\n'+md(r["plan"]["name"]+' · '+plan_summary(r["plan"])+'\nExpires: '+iso(r["expires"]))
            if r.get('key') and use_safe_receipt(s,uid):
                enqueue_api_receipt(s,uid,r,'API created');return True
            rows=ready_url_buttons(r)+[[btn("My APIs","apis","success")]]
        elif action=="apis":
            mine=[a for a in s["apis"].values() if a["owner"]==uid]
            text="*My APIs*\n"+md(f"{len(mine)} endpoints. Manage any endpoint below; all APIs are available in the admin web panel.")
            rows=[[btn(a["name"],"api:"+a["id"],"success" if a["active"] else "danger")] for a in mine][:40]+[[btn("Create API","create"),btn("Home","home")]]
        elif action.startswith("api:"):
            a=owned(s,uid,action.split(":",1)[1]); used=a["used"] if a["day"]==utc_day() else 0
            text="*"+md(a["name"])+"*\n"+md(f"{'Enabled' if a['active'] else 'Paused'} · {used}/{a['daily']} today\n{a['calls']} total attempts · {a['rpm']}/min\nExpires: {iso(a['expires'])}")+"\nEndpoint: "+code(str(cfg("BASE_URL"))+"/api/"+a["id"])
            if a.get("is_trial"):text+="\n"+md(f"TRIAL · {a['calls']}/{a['trial_limit']} total · fixed deadline · no renewal")
            if a.get('plan_snapshot'):text+='\n'+md('Plan: '+a['plan_snapshot']['name']+' · '+plan_summary(a['plan_snapshot']))
            if a.get('total_limit'):text+='\n'+md(f"Total usage: {a['calls']}/{a['total_limit']}")
            rows=api_keyboard(a)
            if simple_ui(s) and not is_admin(uid,s) and a['mode']!='catalog':rows=[[b for b in row if not str(b.get('callback_data','')).startswith('edit:')] for row in rows];rows=[row for row in rows if row]
            if is_admin(uid,s):
                if not a.get('is_trial'):rows.insert(0,[btn('Edit limits / auth','apilimits:'+a['id'])])
                rows.append([btn('All admin APIs','adminapis')])
        elif action.startswith('rename:'):
            a=owned(s,uid,action.split(':',1)[1]);u['flow']={'step':'rename','draft':{},'edit':a['id'],'t':now()}
            text=md('Send the new name (1–60 characters). You will confirm it before saving. No coins charged; time and quota stay unchanged.')
        elif action.startswith("edit:"):
            a=owned(s,uid,action.split(":",1)[1])
            if a["mode"]=="catalog":
                u['flow']={'step':'rename','draft':{},'edit':a['id'],'t':now()}
                text=md('The source is admin-managed. Send a new API name (1–60 characters) to rename this endpoint. /cancel leaves the wizard.')
            else:
                u["flow"]={"step":"data" if a["mode"]=="static" else "url","draft":{k:a.get(k,"") for k in ("name","mode","data","url","param","example_value")},"edit":a["id"],"t":now()}
                text=md("Send replacement JSON." if a["mode"]=="static" else "Send replacement approved HTTPS URL.")
        elif any(action.startswith(x+":") for x in ("rotatecheck","deletecheck","renewcheck")):
            kind,aid=action.split(":",1); a=owned(s,uid,aid); op=kind.replace("check","")
            require(op!="renew" or not a.get("is_trial"),"Trial APIs cannot be renewed. Create a paid API.",409,"TRIAL_IMMUTABLE")
            text=md({"rotate":"Rotate key? The old key stops immediately.","delete":"Permanently delete this API? No balance refund.","renew":f"Extend validity by {a.get('plan_snapshot',{}).get('days',s['settings']['valid_days'])} days for {0 if is_admin(uid,s) else api_price(s,owned(s,uid,aid))[1]} {api_price(s,owned(s,uid,aid))[0]}?"}[op])
            rows=[[btn("Confirm",op+":"+aid,"danger" if op!="renew" else "success"),btn("Cancel","api:"+aid)]]
        elif any(action.startswith(x+":") for x in ("rotate","delete","toggle","renew")):
            op,aid=action.split(":",1); r=api_action(s,uid,aid,op)
            if r.get('key') and use_safe_receipt(s,uid):
                enqueue_api_receipt(s,uid,r,'API key rotated');return True
            text=("*New API key*\n"+code(r["key"])+"\n\n*Ready URL*\n"+code(r["ready_url"])+"\n"+md("Keep private. Example input is prefilled where configured; replace VALUE only for legacy sources.")) if "key" in r else md(r.get("message","Saved.")); rows=ready_url_buttons(r)+[[btn("My APIs","apis")]]
        elif action=="admin":
            actor(s,uid,admin=True)
            text=bot_title(s,"Admin control centre")+"\n\n"+md(f"{len(s['users'])} users · {len(s['apis'])} APIs\n{len(s['outbox'])} pending notifications\nRole: {role(uid,s)}")
            rows=[[btn("Users & permissions","adminusers"),btn("Recent logs","adminlogs")],[btn("Pending referrals","adminrefs"),btn("Full CRUD panel","panel")]]
            rows.append([btn("📊 Admin stats","adminstats")])
            if role(uid,s)=="superadmin":rows[-1].append(btn("Operations","operations"))
            rows.append([btn("Bot appearance","botstyle"),btn("Add source","addsource","success")])
            if role(uid,s)=="superadmin": rows.append([btn("Request backup","backup","success")])
            rows.append([btn('All buttons','commands:0'),btn('Broadcast','broadcast')])
            if focused_ui(s) and not simple_ui(s) and uid in SUPER_IDS:rows.append([btn('Customer inbox','supportinbox')])
            if uid in SUPER_IDS:rows.append([btn('Approvals','approvals'),btn('Force join','forcejoin')])
            rows.append([btn("All APIs / edit","adminapis"),btn("Admin help","adminhelp")])
            rows.append([btn("Home","home")])
        elif action=="adminusers":
            actor(s,uid,admin=True); people=[p for p in s["users"].values() if p["id"].isdigit()][-15:]
            text="*Recent users*\n"+md("Full search, roles, coins and limits are in the web panel.")
            rows=[[btn(p["name"]+" · "+p["id"],"user:"+p["id"])] for p in people]+[[btn("Admin","admin")]]
        elif action.startswith("user:"):
            actor(s,uid,admin=True); target=action.split(":",1)[1]; p=s["users"].get(target); require(p,"User not found.")
            text="*Account*\n"+code(target)+"\n"+md(f"{p['name']} · {role(target,s)}\nCoins: {p['coins']} · Blocked: {p['blocked']}")
            rows=[[btn("Unblock" if p["blocked"] else "Block","block:"+target,"danger"),btn("Panel","panel")],[btn("Admin","admin")]]
        elif action.startswith("block:"):
            target=action.split(":",1)[1]; p=s["users"].get(target); require(p,"User not found.")
            r=admin_action(s,uid,"user",{"id":target,"blocked":not p["blocked"]}); text=md(r["message"]); rows=[[btn("Admin","admin")]]
        elif action=="adminlogs":
            actor(s,uid,admin=True); logs=sorted(s["logs"].values(),key=lambda x:x["t"],reverse=True)[:10]
            text="*Recent audit events*\n"+"\n".join(md(x["event"]+" · "+x["actor"]+" · "+x["detail"][:100]) for x in logs); rows=[[btn("Admin","admin")]]
        elif action=="adminrefs":
            actor(s,uid,admin=True); pending=[(i,r) for i,r in s["referrals"].items() if r["status"]=="pending"][:12]
            text="*Referral review*\n"+md(f"{len(pending)} shown. All entries available in the web panel.")
            rows=[[btn("Approve "+i,"approve:"+i,"success"),btn("Reject","reject:"+i,"danger")] for i,r in pending]+[[btn("Admin","admin")]]
        elif action.startswith("approve:") or action.startswith("reject:"):
            op,rid=action.split(":",1); r=admin_action(s,uid,"referral",{"id":rid,"approve":op=="approve"}); text=md(r["message"]); rows=[[btn("Review more","adminrefs")]]
        elif action=="backup":
            actor(s,uid,superonly=True); s["system"]["backup_requested"]=True
            text=md("Encrypted backup requested. The next scheduler tick will save it and queue the encrypted file for your configured destination (default: verified private logs). The decryption key is never sent. Use Back up now in the admin panel for immediate creation.")
        elif not cb and u.get("flow"):
            f=u["flow"]; require(f.get("t",0)+1800>now(),"Wizard expired. /cancel and start again.")
            d=f["draft"]; step=f["step"]
            if step=='welcome_sticker':
                raise Problem('Send a Telegram sticker, not text or a document. /cancel leaves sticker setup.')
            elif step=='welcome_photo':
                raise Problem('Send the image as a photo, not text or a document. /cancel leaves photo setup.')
            elif step=='convert_amount':
                amount=integer(int(raw),'Diamonds');f['draft']['amount']=amount;f['step']='convert_confirm'
                text=md(f"Convert {amount} diamonds to {amount*f['rate']} coins? One-way conversion.")
                rows=[[btn('Confirm conversion','convertconfirm','success'),btn('Cancel','home')]]
            elif step=='rename':
                require(1<=len(raw)<=60,'Name must be 1–60 characters.')
                owned(s,uid,f['edit']);d['name']=raw;f['step']='confirm'
            elif step=="name":
                require(1<=len(raw)<=60,"Name must be 1–60 characters."); d["name"]=raw
                f["step"]="data" if d["mode"]=="static" else "url"; text=md("Send valid JSON." if d["mode"]=="static" else "Send your approved HTTPS source URL.")
            elif step=="data":
                try: d["data"]=strict_json(raw)
                except ValueError: raise Problem("Invalid JSON. Please resend it.")
                source_validate(d,s["settings"]); f["step"]="confirm"
            elif step=="url":
                d["url"]=raw; d["param"]="value"; source_validate(d,s["settings"]); f["step"]="param"; text=md("Send the input parameter name, for example: value")
            elif step=="param":
                d["param"]=raw; source_validate(d,s["settings"]); f["step"]="example"
                text=md("Send a safe example input value. It will be filled into your complete API URL; do not send a secret or private personal data.")
            elif step=="example":
                d["example_value"]=raw; source_validate(d,s["settings"]); f["step"]="confirm"
            if f["step"]=="confirm":
                cost=0 if f.get("edit") or is_admin(uid,s) else s["settings"]["default_api_price"]
                text=md(f"Confirm {d['name']}? Cost: {cost} coins.")
                rows=[[btn("Confirm","confirmcreate","success"),btn("Cancel","home")]]
        else: text=md("Use /start for the bot menu, /demo for a trial API, /apis to manage APIs, or /cancel to leave a wizard.")
        if u.get("flow") and u.get("flow")!=checkpoint["users"][uid].get("flow"):
            check_data_capacity(s)
    except (Problem,ValueError,TypeError) as e:
        s.clear(); s.update(checkpoint)
        if isinstance(e,Problem) and e.status==403 and not panel_attempt:security_notice(s,'admin_denied',uid,'telegram')
        text="*Action not completed*\n"+md(e.message if isinstance(e,Problem) else "Invalid input. Please try again.")
        if isinstance(e,Problem) and e.status==402:rows=[[btn('💎 Wallet / Buy coins','wallet','success'),btn('🎁 Earn referral coins','refs')],[btn('Other APIs','create'),btn('Home','home')]]
        if s["users"][uid].get("last_bot_error",0)+60<=now():
            s["users"][uid]["last_bot_error"]=now();audit(s,uid,"bot.error",e.code if isinstance(e,Problem) else "INVALID_INPUT")
    if text:
        key=enqueue(s,uid,text,rows)
        if focused_ui(s) and 'handled_support' in locals() and handled_support is not None:
            s['outbox'][key].update(support_private=True,support_target=u.get('flow',{}).get('target'));seal_support_job(s['outbox'][key])
        if focused_ui(s) and not ('handled_support' in locals() and handled_support is not None):u['bot_view']=action.split(':')[0]
        if action in ('panel','confirm','createredeem','creditconfirm','broadcastconfirm') or 'GIFT_' in text:s['outbox'][key]['receipt']=True
    return True

def tg(method,payload=None,files=None):
    require(bool(cfg("BOT_TOKEN")),"Bot token not configured.",503)
    if DEMO: return {"ok":True}
    url="https://api.telegram.org/bot"+str(cfg("BOT_TOKEN"))+"/"+method
    try:
        with outbound_http('POST',url,data=payload if files else None,json=None if files else payload,files=files,
                           timeout=(2,2) if method=='answerCallbackQuery' else (3,8),allow_redirects=False) as r:
            j=r.json()
            if not j.get("ok"): raise TelegramDeliveryError(j.get("error_code",r.status_code),j.get("parameters",{}).get("retry_after",30),telegram_error_reason(j.get('description','')))
            return j.get("result",{})
    except requests.RequestException: raise Problem("Telegram network unavailable.",502) from None

def callback_edit_target(update,job):
    cb=update.get('callback_query')
    if not isinstance(cb,dict) or job.get('kind')!='message' or job.get('photo') or job.get('video') or job.get('receipt'):return None
    message=cb.get('message',{});sender=cb.get('from',{});chat=message.get('chat',{});mid=message.get('message_id')
    if chat.get('type')!='private' or type(mid) is not int or not 0<mid<2**31:return None
    if str(chat.get('id'))!=str(sender.get('id')) or str(chat.get('id'))!=job.get('chat'):return None
    # Preserve key receipts and invoices when their buttons open a new menu.
    content=str(message.get('text') or message.get('caption') or '')
    if any(marker in content for marker in ('Payment received','Refund processed','Referral qualified','Welcome reward','Secure panel login','Owner approval needed')):return None
    if message.get('invoice') or 'GIFT_' in content or 'PRIVATE API CREDENTIALS' in content or re.search(r'\b(?:srd_[A-Za-z0-9_-]+|Droid[A-Za-z0-9_]+)',content):return None
    if job.get('reply_keyboard') or 'Secure panel login' in job.get('text',''):return None
    rows=message.get('reply_markup',{}).get('inline_keyboard',[])
    if any(b.get('copy_text') for row in rows if isinstance(row,list) for b in row if isinstance(b,dict)):return None
    action=str(cb.get('data',''))
    plain={'home','create','apis','refs','wallet','buy','help','developer','mystats','admin','adminstats','adminusers','adminlogs','adminrefs','operations','buttonicons','botstyle','trial','demo','customcreate','adminhelp','paysupport','terms','newstatic','newproxy','convert','redeem','sources','addsource','adminapis'}
    prefixes=('adminapis:','apilimits:','plan:','catalog:','catalogpage:','sourcepreview:','trialpick:','api:','rotatecheck:','deletecheck:','renewcheck:','user:','rename:','edit:','captureicon:')
    plain.update({'starter','starterconfirm','delivery','upgradeconfirm','approvals','forcejoin','joinconfirm','joinremoveconfirm','broadcast','contactbuy','contacthelp','supportinbox','ownerbuy','ownerrequest','deliverydefaultconfirm'})
    prefixes+=('creditpage:','creditbuy:','deliverydefault:','supportview:','supportopen:','supportclose:','supportpage:','supportinbox:','ownerbuy:','ownerpick:','ownerpack:','cmd:','commands:','receiptmode:','starterpick:','upgrades:','upgradepick:','review:','approve:','reject:','joinremove:','broadcastmode:','supportreply:')
    if action not in plain and not action.startswith(prefixes):return None
    caption=bool(message.get('photo') or message.get('video'))
    if caption and text_units(job.get('text',''))>1024:return None
    return {'edit_message_id':mid,'edit_caption':caption}

def deliver_message_job(v):
    if v.get('private_text_enc'):v={**v,'text':fernet().decrypt(v['private_text_enc'].encode()).decode()}
    v=premium_message_job(v)
    payload={'chat_id':v['chat']};editing=bool(v.get('edit_message_id'));caption=bool(v.get('photo') or v.get('video') or editing and v.get('edit_caption'))
    if not v.get('plain_text'):payload['parse_mode']='MarkdownV2'
    if v.get('photo'):payload['photo']=v['photo']
    if v.get('video'):payload.update(video=v['video'],supports_streaming=True)
    payload['caption' if caption else 'text']=v['text'] if caption else v['text'][:4000]
    if not caption:payload['link_preview_options']={'is_disabled':True}
    if v.get('entities'):payload['caption_entities' if caption else 'entities']=v['entities']
    if editing:
        payload['message_id']=v['edit_message_id'];payload['reply_markup']={'inline_keyboard':v.get('keyboard') or []}
        method='editMessageCaption' if caption else 'editMessageText'
    else:
        if v.get('keyboard'):payload['reply_markup']={'inline_keyboard':v['keyboard']}
        if v.get('reply_keyboard'):payload['reply_markup']=v['reply_keyboard']
        method='sendVideo' if v.get('video') else 'sendPhoto' if v.get('photo') else 'sendMessage'
    try:
        result=tg(method,payload)
        entity_field='caption_entities' if caption else 'entities'
        expected=[e for e in payload.get(entity_field,[]) if e.get('type')=='custom_emoji']
        if expected and isinstance(result,dict) and ('text' in result or 'caption' in result):
            returned={(e.get('custom_emoji_id'),e.get('offset'),e.get('length')) for e in result.get(entity_field,[]) if e.get('type')=='custom_emoji'}
            retained=sum((e.get('custom_emoji_id'),e.get('offset'),e.get('length')) in returned for e in expected)
            result={**result,'_srd_emoji_check':{'status':'accepted' if retained==len(expected) else 'stripped' if not retained else 'partial','requested':len(expected),'retained':retained}}
        return result
    except TelegramDeliveryError as exc:
        if editing and exc.api_code==400 and exc.reason=='message_not_modified':return True
        raise

def telegram_error_reason(description):
    text=str(description).lower()
    if 'message is not modified' in text:return 'message_not_modified'
    if any(x in text for x in ('message to edit not found',"message can't be edited",'message cannot be edited','there is no text in the message to edit')):return 'edit_unavailable'
    if 'parse entities' in text or 'entity' in text and 'offset' in text:return 'invalid_format'
    if 'chat not found' in text:return 'chat_not_found'
    if 'blocked' in text:return 'bot_blocked'
    if 'custom emoji' in text or 'custom_emoji' in text:return 'custom_emoji_rejected'
    if 'too many requests' in text:return 'rate_limited'
    if 'query is too old' in text:return 'callback_expired'
    return 'unspecified'

class TelegramDeliveryError(Problem):
    def __init__(self,api_code,retry_after=0,reason='unspecified'):
        super().__init__('Telegram delivery failed ('+str(api_code)+').',502)
        self.reason=reason if reason in ('message_not_modified','edit_unavailable','invalid_format','chat_not_found','bot_blocked','custom_emoji_rejected','rate_limited','callback_expired') else 'unspecified'
        self.api_code=int(api_code);self.retry_after=max(1,min(7*86400,int(retry_after or 30)))

def drain(limit=4,budget=12,chat=None,job_id=None):
    if DEMO:return 0
    chat=str(chat) if chat is not None else None
    interactive={'message','photo','sticker','invoice','joincheck','logverify','joinsetup','api_receipt'}
    sent=0;started=time.monotonic()
    for _ in range(limit):
        if time.monotonic()-started>=budget:break
        token=secrets.token_hex(8);wait_until=[None]
        def claim(s):
            wait_until[0]=None
            sy=s['system']
            if sy.get('telegram_retry_at',0)>now():return
            if sy.get('telegram_send_second')==now() and sy.get('telegram_send_count',0)>=15:return
            items=sorted(s['outbox'].items(),key=lambda kv:(kv[1].get('kind')=='engagement',kv[1].get('priority',0),kv[1]['t']))
            for k,v in items:
                if job_id is not None and k!=job_id:continue
                if chat is not None and (v['chat']!=chat or v.get('kind') not in interactive):continue
                if v.get('kind') in ('joincheck','logverify','joinsetup','commands') and (v.get('expires',0)<=now() or not s['users'].get(v['chat']) or (s['users'][v['chat']].get('blocked') and v.get('kind')!='commands')):
                    del s['outbox'][k];continue
                if v.get('kind')=='backup' and not backup_job_valid(s,v):
                    backup_delivery_status(s,k,v,'cancelled');del s['outbox'][k];continue
                if v.get('kind')=='joincheck' and v.get('revision')!=join_revision(s):del s['outbox'][k];continue
                if v.get('kind')=='opslog' and (v['chat']!=s['settings'].get('log_channel') or sy.get('log_disabled')):
                    del s['outbox'][k];continue
                if v.get('kind')=='approval':
                    approval=s['approvals'].get(v.get('approval_id'))
                    if v['chat'] not in SUPER_IDS or not approval or approval['status']!='pending' or approval['expires']<=now() or s['users'].get(v['chat'],{}).get('blocked'):
                        del s['outbox'][k];continue
                if v.get('kind')=='admin_event' and (not s['settings'].get('admin_event_notifications') or not is_admin(v['chat'],s) or s['users'].get(v['chat'],{}).get('blocked')):
                    del s['outbox'][k];continue
                if v.get('kind')=='api_receipt':
                    endpoint=s['apis'].get(v.get('receipt_api_id'))
                    if not endpoint or endpoint.get('key_hash')!=v.get('receipt_key_hash'):
                        del s['outbox'][k];continue
                if v.get('kind')=='sticker':
                    if v.get('expires',0)<=now() or v.get('sticker')!=s['settings'].get('welcome_sticker'):
                        del s['outbox'][k];continue
                    if v.get('after') in s['outbox']:continue
                if v.get('lease',0)>=now():continue
                if focused_ui(s) and any(other is not v and other.get('chat')==v['chat'] and other.get('lease',0)>now() for other in s['outbox'].values()):continue
                u=s['users'].get(v['chat'])
                if v.get('support_private') and simple_ui(s):del s['outbox'][k];continue
                if v.get('support_private'):
                    target=v.get('support_target')
                    if not u or u.get('blocked') or (target and v['chat']!=target and v['chat'] not in SUPER_IDS) or (not target and v['chat'] not in SUPER_IDS):
                        del s['outbox'][k];continue
                if focused_ui(s) and v.get('nav') and u:
                    if v.get('nav_epoch',0)!=u.get('nav_epoch',0):del s['outbox'][k];continue
                    if u.get('nav_recovery_pending'):
                        v.pop('edit_message_id',None);v.pop('edit_caption',None);v.pop('photo',None);v.pop('video',None);v['kind']='message'
                    anchor={} if u.get('nav_recovery_pending') else u.get('bot_nav',{})
                    if valid_nav(anchor) and not v.get('needs_text_anchor') and not v.get('edit_fallback'):
                        if not anchor.get('caption') or v.get('screen_units',text_units(v.get('text','')))<=1024:
                            v.pop('photo',None);v.pop('video',None);v['kind']='message';v.update(edit_message_id=anchor['id'],edit_caption=bool(anchor.get('caption')))
                if v.get('kind')=='engagement':
                    if not promo_valid(s,v):drop_promo(s,k);continue
                    wait=promo_wait(s,u)
                    if wait>now():v['next']=max(v.get('next',0),wait);continue
                elif u and u.get('telegram_blocked') and v.get('kind') not in ('commands','logverify'):
                    del s['outbox'][k];continue
                chats=sy.setdefault('telegram_chat_next',{})
                due=v.get('next',0) if v['kind']=='logverify' else max(v.get('next',0),chats.get(v['chat'],0),u.get('telegram_next_send',0) if u else 0)
                if due>now():
                    if chat is not None and due<=now()+2:
                        wait_until[0]=min(wait_until[0] or due,due)
                    continue
                chats[v['chat']]=now()+1
                if len(chats)>256:sy['telegram_chat_next']={chat:t for chat,t in chats.items() if t>now()}
                if sy.get('telegram_send_second')!=now():sy.update(telegram_send_second=now(),telegram_send_count=0)
                sy['telegram_send_count']=sy.get('telegram_send_count',0)+1
                if u:u['telegram_next_send']=now()+1
                if sy.get('supplied_emoji_disabled_until',0)>now() or not s['settings'].get('supplied_emoji_enabled'):
                    v['premium_emojis']=False
                    for ri,bi in v.get('auto_emoji_buttons',[]):
                        try:v['keyboard'][ri][bi].pop('icon_custom_emoji_id',None)
                        except (IndexError,KeyError,TypeError):pass
                v.update(lease=now()+60,lease_id=token)
                return k,copy.deepcopy(v)
        item=store.tx(claim)
        # A short per-chat cooldown should not push a requested reply/sticker to minute cron.
        # Never wait out Telegram 429, network backoff or another worker's active lease.
        if not item and chat is not None and wait_until[0] is not None and time.monotonic()-started+2.1<budget:
            time.sleep(min(2.05,max(0.05,wait_until[0]-time.time()+0.025)))
            item=store.tx(claim)
        if not item:break
        k,v=item;success=False;error=None;job_result=None
        try:
            if v['kind']=='commands':
                current_state=store.read();items=commands_for(current_state,v['chat'])
                tg('setMyCommands',{'scope':{'type':'chat','chat_id':int(v['chat'])},'commands':items})
                job_result=digest(json.dumps(items,sort_keys=True))
            elif v['kind']=='joincheck':job_result=join_probe(store.read(),v)
            elif v['kind']=='logverify':job_result=log_probe(v)
            elif v['kind']=='joinsetup':job_result=join_setup_probe(v)
            elif v['kind']=='invoice':
                o=store.read()['orders'].get(v['backup'])
                if o and o['status']=='pending':tg('sendInvoice',invoice_payload(o))
            elif v['kind']=='sticker':
                tg('sendSticker',{'chat_id':v['chat'],'sticker':v['sticker'],'disable_notification':True})
            elif v['kind']=='api_receipt':
                plaintext=fernet().decrypt(v['receipt_enc'].encode())
                payload={'chat_id':v['chat'],'caption':v['text'],'reply_markup':json.dumps({'inline_keyboard':v.get('keyboard') or []})}
                if v.get('receipt_format')=='chat_url':
                    body=json.loads(plaintext.decode());require(isinstance(body,dict) and isinstance(body.get('text'),str),'Invalid credential payload.')
                    job_result=tg('sendMessage',{'chat_id':v['chat'],'text':body['text'],'entities':body['entities'],
                                               'link_preview_options':{'is_disabled':True},'reply_markup':{'inline_keyboard':v.get('keyboard') or []}})
                elif v.get('receipt_format')=='text':
                    text=plaintext.decode()
                    tg('sendMessage',{'chat_id':v['chat'],'text':text,'entities':[{'type':'pre','offset':0,'length':text_units(text)}],
                                     'link_preview_options':{'is_disabled':True},'reply_markup':{'inline_keyboard':v.get('keyboard') or []}})
                else:tg('sendDocument',payload,files={'document':(v['filename'],plaintext,'text/plain; charset=utf-8')})
            elif v['kind']=='backup':
                require(backup_job_valid(store.read(),v),'Backup destination changed; delivery cancelled.',409,'BACKUP_DESTINATION_CHANGED')
                if v.get('backup_route')=='logs':
                    try:log_probe({'target':v['chat']})
                    except Problem as exc:
                        if exc.status<500:raise Problem('Re-verify the private log destination.',403,'BACKUP_LOG_UNVERIFIED')
                        raise
                blob=load_backup(v['backup'])
                require(backup_job_valid(store.read(),v),'Backup destination changed; delivery cancelled.',409,'BACKUP_DESTINATION_CHANGED')
                tg('sendDocument',{'chat_id':v['chat'],'caption':'SR DARK encrypted backup. Keep your backup key offline.'},files={'document':(v['backup']+'.enc',blob,'application/octet-stream')})
            else:
                job_result=deliver_message_job(v)
            success=True
            if v['kind'] not in ('joincheck','logverify','joinsetup','commands'):sent+=1
        except Exception as exc:
            error=exc;LOG.warning('Telegram delivery unsuccessful; queue policy applied')
        def finish(s):
            current=s['outbox'].get(k)
            if not current or current.get('lease_id')!=token:return
            u=s['users'].get(v['chat']);c=s['campaigns'].get(v.get('campaign_id'))
            if success:
                check=job_result.get('_srd_emoji_check') if isinstance(job_result,dict) else None
                if check:
                    s['system']['supplied_emoji_delivery']={**check,'t':now()}
                    if check['status']!='accepted':
                        if v.get('premium_emojis'):s['system']['supplied_emoji_disabled_until']=now()+3600
                        if s['system'].get('emoji_silent_warn_at',0)+3600<=now():
                            s['system']['emoji_silent_warn_at']=now()
                            ops_log(s,'Custom emoji not retained','system','Message delivered, but Telegram removed custom emoji. Check actual BotFather owner Premium/Fragment eligibility. Automatic theme paused for one hour; no resend.')
                if v.get('nav') and u and v.get('nav_epoch',0)==u.get('nav_epoch',0):
                    mid=v.get('edit_message_id') or (job_result.get('message_id') if isinstance(job_result,dict) else None)
                    if type(mid) is int:
                        u['bot_nav']={'id':mid,'caption':bool(v.get('photo') or v.get('video') or v.get('edit_caption')),'t':now()};u.pop('nav_recovery_pending',None)
                        u['bot_last_response']={'at':now(),'update_id':v.get('request_update_id'),'message_id':mid,'mode':'edit' if v.get('edit_message_id') else 'new'}
                if v.get('log_check_id') and s['system'].get('log_check',{}).get('job_id')==v['log_check_id']:
                    s['system']['log_check']['test_sent']=True
                if v['kind']=='backup':
                    backup_delivery_status(s,k,v,'sent');ops_log(s,'backup.delivered','scheduler','Encrypted file delivered; decryption key was not sent.')
                if v['kind']=='commands':
                    del s['outbox'][k]
                    if u:
                        u['command_menu_hash']=job_result
                        if digest(json.dumps(commands_for(s,v['chat']),sort_keys=True))!=job_result:queue_commands(s,v['chat'],force=True)
                    return
                if v['kind']=='joincheck':
                    checkpoint=copy.deepcopy(s)
                    try:join_finish(s,k,v,job_result)
                    except Problem:
                        s.clear();s.update(checkpoint);s['outbox'].pop(k,None)
                        soft_message(s,v['chat'],md('Onboarding could not finish. No new reward was committed. Contact the owner and retry after the account/capacity issue is resolved.'))
                        ops_log(s,'forcejoin.finalization.error',v['chat'],'Atomic onboarding failed; review account/capacity.')
                    return
                if v['kind']=='joinsetup':
                    del s['outbox'][k]
                    try:finish_join_setup(s,v,job_result)
                    except Problem as exc:soft_message(s,v['chat'],md(exc.message),[[btn('Choose again','forcejoin')]])
                    return
                if v['kind']=='logverify':
                    del s['outbox'][k]
                    check={'job_id':k,'target':v['target'],'state':'cancelled','t':now(),'message':'Destination or owner permissions changed; verify again.'}
                    s['system']['log_check']=check
                    if not u or u.get('blocked') or role(v['chat'],s)!='superadmin':return
                    if v['target'] in {c['chat_id'] for c in s['settings']['force_join_channels']}:return
                    if v.get('set_destination') and role(v['chat'],s)=='superadmin' and s['settings'].get('log_channel','')==v.get('previous_destination'):
                        s['settings']['log_channel']=v['target']
                        audit(s,v['chat'],'operations.log-destination','Verified private group selected')
                    if v['target']==s['settings'].get('log_channel') and is_admin(v['chat'],s) and role(v['chat'],s)=='superadmin':
                        s['system'].update(log_verified=v['target'],log_disabled=False)
                        proof=ops_log(s,'✅ Log channel verified',v['chat'],'Private operational logs enabled; no API keys or lookup values are forwarded.')
                        check.update(state='verified',message='Private logs verified.',proof_job=proof,test_sent=False)
                        if proof:s['outbox'][proof]['log_check_id']=k
                        soft_message(s,v['chat'],md('Private log destination verified. Heartbeat/daily reports require a running worker or authenticated external scheduler.'))
                    return
                if v['kind']=='engagement':
                    if u:
                        _,_,day=delivery_window(s['settings'])
                        u['promo_count']=(u.get('promo_count',0) if u.get('promo_day')==day else 0)+1
                        u.update(promo_day=day,promo_last_sent=now())
                        if u.get('promo_pending')==k:u['promo_pending']=''
                        if c and c['trigger']!='random' and c['revision']==v['revision']:
                            history=u.setdefault('campaign_events',{})
                            if c['trigger']=='expiry':
                                if not isinstance(history.get(c['id']),dict):history[c['id']]={}
                                history[c['id']][v['event_target']]=v['fingerprint']
                            else:history[c['id']]=v['fingerprint']
                    if c:c['sent']+=1
                del s['outbox'][k];return
            current['tries']+=1;current['lease']=0
            api_code=getattr(error,'api_code',0)
            s['system']['last_telegram_error']={'t':now(),'code':api_code,'kind':v['kind'],'reason':getattr(error,'reason','unspecified')}
            if v['kind']!='opslog' and s['system'].get('delivery_error_log_at',0)+300<=now():
                s['system']['delivery_error_log_at']=now();ops_log(s,'telegram.delivery.error',v['chat'],v['kind']+' · code '+str(api_code or 'transport')+' · retry/fallback policy applies')
            if c:c['last_error']='Telegram '+str(api_code or 'network error')
            if v['kind']=='backup' and getattr(error,'code','')=='BACKUP_DESTINATION_CHANGED':
                backup_delivery_status(s,k,v,'cancelled');s['outbox'].pop(k,None);return
            if v['kind']=='backup' and api_code!=429:current['backup_failures']=current.get('backup_failures',0)+1
            if v['kind']=='backup' and api_code!=429 and (api_code in (400,403) or isinstance(error,Problem) and error.status<500 or current.get('backup_failures',0)>=3):
                backup_delivery_status(s,k,v,'failed');s['outbox'].pop(k,None)
                s['system']['backup_delivery_warning']='Encrypted Telegram file delivery failed; the saved backup remains in storage. Check permissions and use Back up now to retry.'
                if v.get('backup_route')=='logs' and s['settings'].get('log_channel')==v['chat'] and (api_code in (400,403) or getattr(error,'code','')=='BACKUP_LOG_UNVERIFIED'):s['system']['log_disabled']=True
                audit(s,'scheduler','backup.delivery.failed','No plaintext/key sent. Check private log verification, permissions and storage.')
                return
            if v['kind']=='commands' and api_code!=429 and (api_code in (400,403) or current['tries']>=3):
                del s['outbox'][k];return
            if v['kind']=='logverify':
                s['system']['log_check']={'job_id':k,'target':v['target'],'state':'waiting','t':now(),'message':log_check_error(error)}
            if v['kind']=='joinsetup' and api_code!=429 and (api_code in (400,403) or isinstance(error,Problem) and error.status<500 or current['tries']>=3):
                del s['outbox'][k];soft_message(s,v['chat'],md('Could not verify this selection. Both you and the bot must be administrators. Select again.'),[[btn('Choose again','forcejoin')]]);return
            if v['kind'] in ('joincheck','logverify') and api_code!=429:
                if api_code in (400,403) or isinstance(error,Problem) and api_code==0 and error.status<500 or current['tries']>=3:
                    del s['outbox'][k]
                    if v['kind']=='logverify':
                        s['system']['log_check']['state']='failed'
                        if s['system'].get('log_verified')==v['target']:s['system']['log_disabled']=True
                    soft_message(s,v['chat'],md(log_check_error(error) if v['kind']=='logverify' else 'Verification unavailable. Check bot admin permissions, channel IDs and membership, then retry. No membership reward was granted.'))
                    ops_log(s,'verification.error',v['chat'],v['kind']);return
            if v['kind']=='opslog' and (api_code==403 or api_code==400 and (not focused_ui(s) or getattr(error,'reason','')=='chat_not_found')):
                if v.get('log_check_id') and s['system'].get('log_check',{}).get('job_id')==v['log_check_id']:
                    s['system']['log_check'].update(state='failed',message='Telegram rejected the verification test message. Check bot permissions, then verify again.',test_sent=False)
                s['system']['log_disabled']=True;s['outbox'].pop(k,None);return
            if api_code==403:
                if u:u.update(telegram_blocked=True,updates_on=False)
                if v['kind']=='engagement':drop_promo(s,k,'failed')
                else:del s['outbox'][k]
                cancel_promos(s,uid=v['chat']);return
            if v['kind']=='api_receipt' and api_code!=429 and (api_code!=400 and current['tries']>=5):
                del s['outbox'][k]
                soft_message(s,v['chat'],md('Credential delivery failed. Use My APIs → Rotate key to issue a new private receipt. No extra purchase is needed.' if v.get('receipt_format') in ('text','chat_url') else 'TXT delivery failed. Use My APIs → Rotate key to issue a new private file. No extra purchase is needed.'),[[btn('My APIs','apis')]])
                return
            if api_code==400:
                if current.get('edit_message_id') and getattr(error,'reason','')=='edit_unavailable':
                    if u and u.get('bot_nav',{}).get('id')==current.get('edit_message_id'):u.pop('bot_nav',None)
                    current.pop('edit_message_id',None);current.pop('edit_caption',None)
                    current.update(edit_fallback=True,next=now()+1)
                    return
                icons=any(b.get('icon_custom_emoji_id') for row in current.get('keyboard') or [] for b in row)
                custom=any(e.get('type')=='custom_emoji' for e in current.get('entities',[])) or bool(current.get('premium_emojis') and not current.get('emoji_fallback'))
                if (icons or custom) and not current.get('emoji_fallback'):
                    if (current.get('premium_emojis') or current.get('auto_emoji_buttons')) and getattr(error,'reason','')=='custom_emoji_rejected':s['system']['supplied_emoji_disabled_until']=now()+3600
                    for row in current.get('keyboard') or []:
                        for b in row:b.pop('icon_custom_emoji_id',None)
                    current['entities']=[e for e in current.get('entities',[]) if e.get('type')!='custom_emoji']
                    current.update(emoji_fallback=True,next=now()+2);return
                if getattr(error,'reason','')=='invalid_format' and not current.get('format_fallback') and v['kind'] in ('message','photo','engagement','opslog','admin_event'):
                    current.update(plain_text=True,entities=[],format_fallback=True,next=now()+1)
                    s['system']['last_telegram_error']['fallback']='Plain-text retry queued; copy buttons retain original URLs.'
                    return
                if v['kind']=='api_receipt':
                    del s['outbox'][k]
                    soft_message(s,v['chat'],md('Credential delivery failed. Use My APIs → Rotate key for a new private receipt.' if v.get('receipt_format') in ('text','chat_url') else 'TXT delivery failed. Use My APIs → Rotate key for a new private file.'),[[btn('My APIs','apis')]])
                    return
                if v['kind']=='sticker':
                    if s['settings'].get('welcome_sticker')==v.get('sticker'):
                        s['settings'].update(welcome_sticker='',welcome_sticker_info={})
                        audit(s,'system','welcome.sticker.invalid','Telegram rejected sticker; select another with /setsticker')
                    clear_welcome_stickers(s)
                    s['system']['last_telegram_error']['fallback']='Sticker disabled; welcome photo/text retained. Use /setsticker.'
                elif v['kind']=='photo':
                    current['kind']='message';current.pop('photo',None);current['next']=now()+2
                    s['system']['last_telegram_error']['fallback']='Welcome/preview text queued; re-upload photo with /setwelcome.'
                elif v['kind']=='engagement':
                    drop_promo(s,k,'failed')
                    if c:c['enabled']=False;c['run']=None;cancel_promos(s,cid=c['id'])
                else:del s['outbox'][k]
                return
            if api_code==429:
                wait=getattr(error,'retry_after',30);s['system']['telegram_retry_at']=now()+wait
                current['next']=now()+wait;return
            if v['kind'] in ('sticker','opslog') and current['tries']>=3:
                del s['outbox'][k];return
            if v['kind']=='engagement' and (current['tries']>=5 or current['t']+86400<=now()):drop_promo(s,k,'failed');return
            current['next']=now()+min(3600,30*2**min(current['tries'],7))
        def finish_and_pending(state):
            finish(state)
            return any(j['chat']==chat and j.get('kind') in interactive for j in state['outbox'].values()) if chat is not None else True
        if not store.tx(finish_and_pending):break
    return sent

def configure_webhook():
    require(store is not None and not DEMO,"Configure production credentials first.",503)
    try:connections=int(cfg('TELEGRAM_WEBHOOK_CONNECTIONS'))
    except (ValueError,TypeError):raise Problem('TELEGRAM_WEBHOOK_CONNECTIONS must be 1–16.')
    require(1<=connections<=16,'TELEGRAM_WEBHOOK_CONNECTIONS must be 1–16.')
    me=tg("getMe",{})
    require(me.get("is_bot") is True and isinstance(me.get("id"),int) and
        bool(re.fullmatch(r"[A-Za-z0-9_]{5,32}",str(me.get("username","")))),
        "Token verification did not return a valid bot identity.",502)
    identity={"id":me["id"],"username":me["username"],"token_fingerprint":digest(cfg("BOT_TOKEN"))}
    store.tx(lambda s:s["system"].update(bot_identity=identity))
    with _IDENTITY_LOCK:
        _IDENTITY_CACHE.update(username=me["username"],until=now()+60)
    result=tg("setWebhook",{"url":str(cfg("BASE_URL")).rstrip("/")+"/telegram/webhook",
        "secret_token":str(cfg("WEBHOOK_SECRET")),"max_connections":connections,"allowed_updates":["message","callback_query","pre_checkout_query"],"drop_pending_updates":False})
    tg('setMyCommands',{'scope':{'type':'default'},'commands':[{'command':c,'description':d} for c,d in (SIMPLE_COMMANDS if simple_ui(store.read()) else USER_COMMANDS)]})
    def scopes(state):
        for uid,u in state['users'].items():
            if uid.isdigit() and u.get('telegram_started') and (is_admin(uid,state) or u.get('command_menu_hash')):queue_commands(state,uid,force=True)
    store.tx(scopes)
    return result

@app.post("/ops/webhook")
def configure_webhook_route():
    require(store is not None and not DEMO,"Setup unavailable.",503)
    require(hmac.compare_digest(request.headers.get("Authorization",""),"Bearer "+str(cfg("CRON_SECRET"))),"Invalid operator secret.",403)
    configure_webhook()
    return jsonify(ok=True,username=bot_username(),message="Bot verified; webhook and command menu registered.")

@app.post("/telegram/webhook")
def webhook():
    global _BOT_TIMINGS
    require(store is not None and not DEMO,"Webhook unavailable.",503)
    require(hmac.compare_digest(request.headers.get("X-Telegram-Bot-Api-Secret-Token",""),str(cfg("WEBHOOK_SECRET"))),"Invalid webhook secret.",403)
    update=body()
    if update.get('pre_checkout_query'):
        # Direct Bot API webhook response avoids queue/network delay before Telegram's 10-second deadline.
        return jsonify(store.tx(lambda s:precheckout(s,update['pre_checkout_query'])))
    message=update.get('message',{})
    if message.get('successful_payment') or message.get('refunded_payment'):
        store.tx(lambda s:apply_payment(s,message,refund=bool(message.get('refunded_payment'))))
        return jsonify(ok=True)  # charge-ID dedupe, independent of normal update watermark/flood guard
    cb=update.get("callback_query")
    if cb and not background_worker_requested():
        # Clear the button spinner before the RTDB round trip; no business success is asserted.
        try: tg("answerCallbackQuery",{"callback_query_id":cb["id"]})
        except Exception: pass
    incoming=cb.get('message',{}) if isinstance(cb,dict) else message
    sender=cb.get('from',{}) if isinstance(cb,dict) else message.get('from',{})
    chat=incoming.get('chat',{})
    reply_chat=str(sender['id']) if chat.get('type')=='private' and not sender.get('is_bot') and str(sender.get('id','')).isdigit() and str(chat.get('id'))==str(sender['id']) else None
    if (not cb and chat.get('type') in ('group','supergroup') and str(sender.get('id')) in SUPER_IDS
        and re.fullmatch(r'/loghere(?:@[A-Za-z0-9_]+)?',str(message.get('text','')).strip(),re.I)):
        reply_chat=str(sender['id'])
    def process_and_prioritize(state):
        before=set(state['outbox']);checks=[];group_replies=[];setup_jobs=[]
        result=process_bot(state,update)
        for key in [k for k in state['outbox'] if k not in before]:
            if key not in state['outbox']:continue
            job=state['outbox'][key]
            job['request_update_id']=str(update.get('update_id',''))
            if job.get('kind')=='logverify':checks.append(key)
            if job.get('kind')=='joinsetup':setup_jobs.append(key)
            if job.get('group_help'):group_replies.append(key)
            if job['chat']==reply_chat and job.get('kind') in ('message','photo','sticker','invoice','joincheck','logverify','joinsetup','api_receipt'):
                job['priority']=min(job.get('priority',0),-2)
                target=callback_edit_target(update,job)
                if v415_enabled(state) and not focused_ui(state) and job.get('kind') in ('message','photo') and not str(cb.get('data','') if cb else '').startswith(('approve:','reject:','broadcastconfirm')) and not job.get('receipt') and not job.get('reply_keyboard') and not any(x in job.get('text','') for x in ('Secure panel login','one-time code','confirmation code','New API key')):
                    job['nav']=True
                    anchor=state['users'].get(reply_chat,{}).get('bot_nav',{})
                    if not cb and job.get('kind')=='message' and anchor.get('t',0)+86400>now() and anchor.get('id') and (not anchor.get('caption') or text_units(job['text'])<=1024):
                        target={'edit_message_id':anchor['id'],'edit_caption':anchor.get('caption',False)}
                if focused_ui(state):
                    nav_job(state,key,reply_chat,update);target=None
                if target:
                    job.update(target)
                    for previous,pending in list(state['outbox'].items()):
                        if previous in before and pending.get('chat')==reply_chat and pending.get('edit_message_id')==target['edit_message_id'] and pending.get('lease',0)<now():
                            del state['outbox'][previous]
        return result,checks,group_replies,setup_jobs,v415_enabled(state)
    started=time.monotonic()
    _,checks,group_replies,setup_jobs,modern=store.tx(process_and_prioritize)
    for key in setup_jobs:drain(1,8,job_id=key)
    for key in checks:run_requested_log_check(key)
    for key in group_replies:drain(1,6,job_id=key)
    database_done=time.monotonic()
    wake_worker()
    if reply_chat is not None:
        if not (modern and worker_available()):drain(1,3,reply_chat) if modern and background_worker_requested() else drain(3,6,reply_chat)
    finished=time.monotonic()
    _BOT_TIMINGS={'at':now(),'database_ms':round((database_done-started)*1000),'delivery_ms':round((finished-database_done)*1000)}
    if finished-started>3:
        LOG.warning('Slow bot webhook: database_ms=%d delivery_ms=%d',int((database_done-started)*1000),int((finished-database_done)*1000))
    response=jsonify(method='answerCallbackQuery',callback_query_id=cb['id']) if cb and background_worker_requested() else jsonify(ok=True)
    response.headers['X-Bot-Database-Ms']=str(_BOT_TIMINGS['database_ms']);response.headers['X-Bot-Delivery-Ms']=str(_BOT_TIMINGS['delivery_ms'])
    return response

# Encrypted snapshots. No bot tokens/service account/secret config included.
def fernet():
    key=cfg("BACKUP_KEY") or base64.urlsafe_b64encode(hashlib.sha256((secret+"/srdark-backup-v4").encode()).digest()).decode()
    return Fernet(key.encode() if isinstance(key,str) else key)
def backup_blob():
    snap=store.read()
    # Login codes and queued one-time keys are deliberately not exported.
    snap["outbox"]={}; snap["login_codes"]={}; snap["login_limits"]={}
    snap["sessions"]={}; snap["challenges"]={};snap["approvals"]={}
    snap["system"].pop("worker_tick_lease",None)
    for u in snap["users"].values(): u["flow"]={}; u["promo_pending"]=""
    for c in snap["campaigns"].values():c["run"]=None
    snap["system"].pop("backup_lease",None)
    raw=json.dumps({"format":"srdark-encrypted-v4","created":now(),"state":snap},ensure_ascii=False,allow_nan=False).encode()
    require(len(raw)<3*1024*1024,"Snapshot exceeds 3MB small-install safety cap.",413)
    return fernet().encrypt(raw)

def s3_client():
    import boto3
    from botocore.config import Config
    return boto3.client("s3",endpoint_url=cfg("S3_ENDPOINT_URL") or None,region_name=cfg("S3_REGION") or "auto",
        aws_access_key_id=cfg("S3_ACCESS_KEY") or None,aws_secret_access_key=cfg("S3_SECRET_KEY") or None,
        config=Config(connect_timeout=3,read_timeout=8,retries={"max_attempts":1}))

def save_cloud(key,blob,keep):
    if cfg("S3_BUCKET") and not DEMO:
        client=s3_client(); bucket=str(cfg("S3_BUCKET")); client.put_object(Bucket=bucket,Key="srdark/"+key+".enc",Body=blob,ContentType="application/octet-stream")
        objects=[]
        for page in client.get_paginator("list_objects_v2").paginate(Bucket=bucket,Prefix="srdark/"):
            objects.extend(o["Key"] for o in page.get("Contents",[]) if o["Key"].endswith(".enc"))
        for old in sorted(objects)[:-keep]: client.delete_object(Bucket=bucket,Key=old)
        return "S3/R2"
    return ""
def load_backup(key):
    require(bool(re.fullmatch(r"[0-9A-Za-z_-]+",key)),"Invalid backup ID.")
    try: return store.get_backup(key)
    except Exception:
        require(bool(cfg("S3_BUCKET")),"Backup unavailable.",404)
        return s3_client().get_object(Bucket=str(cfg("S3_BUCKET")),Key="srdark/"+key+".enc")["Body"].read()

# Encrypted attachments have destination-bound, bounded delivery jobs.
def backup_job_valid(s,v):
    st=s['settings'];route=v.get('backup_route','owner');mode=st.get('backup_delivery','logs')
    if v.get('expires',v['t']+86400)<=now():return False
    if route=='owner':return mode in ('owner','both') and v['chat'] in SUPER_IDS and not s['users'].get(v['chat'],{}).get('blocked')
    dest=st.get('log_channel','')
    return (route=='logs' and mode in ('logs','both') and bool(re.fullmatch(r'-[1-9][0-9]{4,19}',dest))
            and v['chat']==dest and s['system'].get('log_verified')==dest and not s['system'].get('log_disabled')
            and dest not in {c['chat_id'] for c in st['force_join_channels']})

def backup_delivery_status(s,k,v,status):
    marks=s['system'].setdefault('backup_dispatch',{})
    mark=marks.get(v['chat'])
    if mark and mark.get('job')==k:mark.update(status=status,at=now())
    if status=='sent':s['system']['last_backup_delivered']={'id':v['backup'],'chat':v['chat'],'at':now()}

def queue_backup_deliveries(s,key):
    st=s['settings'];sy=s['system'];mode=st.get('backup_delivery','logs');targets=[];warnings=[]
    if not key or sy.get('last_backup',0)+86400<=now():return 0
    if mode in ('owner','both'):
        targets.extend((uid,'owner') for uid in sorted(SUPER_IDS) if not s['users'].get(uid,{}).get('blocked'))
        if not SUPER_IDS:warnings.append('No Telegram owner ID configured for backup delivery')
    if mode in ('logs','both'):
        dest=st.get('log_channel','')
        probe={'chat':dest,'backup_route':'logs','t':now(),'expires':now()+86400}
        if backup_job_valid(s,probe):targets.append((dest,'logs'))
        else:warnings.append('Encrypted file saved; verify the private logs destination before Telegram delivery')
    # Keep only currently selected recipients; cancelled/in-flight jobs are rechecked before sending.
    marks=sy.setdefault('backup_dispatch',{});allowed={chat for chat,_ in targets}
    for chat in list(marks):
        if chat not in allowed:marks.pop(chat,None)
    queued=0
    for chat,route in targets:
        mark=marks.get(chat,{})
        if mark.get('key')==key and mark.get('status') in ('queued','sent','failed'):
            if mark.get('status')=='failed':warnings.append('Encrypted Telegram file delivery failed; check permissions/storage and use Back up now to retry')
            continue
        if len(s['outbox'])>=1900:warnings.append('Telegram queue busy; backup delivery will retry on a later scheduler tick');continue
        for old,v in list(s['outbox'].items()):
            if v.get('kind')=='backup' and v['chat']==chat and v.get('lease',0)<=now():s['outbox'].pop(old,None)
        k=enqueue(s,chat,'',kind='backup',backup=key)
        s['outbox'][k].update(backup_route=route,expires=now()+86400)
        marks[chat]={'key':key,'job':k,'route':route,'status':'queued','at':now()};queued+=1
    sy['backup_delivery_warning']='; '.join(dict.fromkeys(warnings))
    return queued


def run_backup(force=False):
    lease=secrets.token_hex(8)
    def claim(s):
        sy=s["system"]; current=sy.get("backup_lease",{})
        if current.get("until",0)>now(): return False
        if not force and not sy.get("backup_requested") and sy.get("last_backup",0)+s["settings"]["backup_hours"]*3600>now(): return False
        sy["backup_lease"]={"id":lease,"until":now()+180}; return True
    if not store.tx(claim): return {"message":"Backup not due or already in progress."}
    key=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f")+"_"+secrets.token_hex(3)
    try:
        st=store.read()["settings"]; blob=backup_blob(); locations=[]; warnings=[]
        try: store.put_backup(key,blob,st["backup_keep"]); locations.append("Firebase" if store.kind=="firebase" else "local disk")
        except Exception: warnings.append("Primary backup destination failed")
        if cfg("S3_BUCKET"):
            try:
                loc=save_cloud(key,blob,st["backup_keep"])
                if loc: locations.append(loc)
            except Exception: warnings.append("S3/R2 destination failed")
        require(bool(locations),"All backup destinations failed.",503)
        def done(s):
            sy=s["system"]
            if sy.get("backup_lease",{}).get("id")!=lease:return None
            sy.update(last_backup=now(),backup_id=key,backup_locations=locations,backup_warning="; ".join(warnings),backup_requested=False)
            sy.pop("backup_lease",None)
            queued=queue_backup_deliveries(s,key)
            audit(s,"scheduler","backup.saved",", ".join(locations))
            return queued
        queued=store.tx(done)
        if queued is None:return {"message":"Encrypted snapshot saved; a newer backup job owns delivery scheduling.","id":key,"destinations":locations,"warnings":warnings,"telegram_queued":0,"superseded":True}
        return {"message":"Encrypted backup saved; Telegram file delivery queued." if queued else "Encrypted backup saved; Telegram file delivery is pending destination verification or queue availability.","id":key,"destinations":locations,"warnings":warnings,"telegram_queued":queued}
    except Exception:
        def fail(s):
            if s["system"].get("backup_lease",{}).get("id")!=lease:return
            s["system"].pop("backup_lease",None); s["system"]["backup_warning"]="Backup failed; check database/cloud availability."
            audit(s,"scheduler","backup.failed")
        try: store.tx(fail)
        except Exception: pass
        raise

def validate_restore(blob):
    try: o=json.loads(fernet().decrypt(blob))
    except (InvalidToken,ValueError): raise Problem("Invalid encrypted backup or wrong backup key.")
    require(o.get("format")=="srdark-encrypted-v4" and o.get("state",{}).get("schema")==4,"Only SR DARK v4 snapshots can be restored. Legacy HTML backups require migration.")
    s=normalize(o["state"])
    require(isinstance(s.get('starter_claims'),dict) and len(s['starter_claims'])<=3000,'Invalid starter history.')
    for uid,claim in s['starter_claims'].items():
        require(isinstance(uid,str) and uid.isdigit() and isinstance(claim,dict),'Invalid starter claim.')
        require(all(type(claim.get(k)) is int and claim[k]>=0 for k in ('claimed_at','expires')) and claim['expires']>=claim['claimed_at'],'Invalid starter claim times.')
        require(all(isinstance(claim.get(k),str) and len(claim[k])<=80 for k in ('api_id','catalog_id')),'Invalid starter claim identifiers.')
    require(isinstance(s.get('support_threads'),dict) and len(s['support_threads'])<=100,'Invalid support history.')
    require(len(json.dumps(s['support_threads']).encode())<=512*1024,'Support history budget exceeded.')
    for uid,thread in s['support_threads'].items():
        require(isinstance(uid,str) and uid.isdigit() and isinstance(thread,dict) and thread.get('uid')==uid and isinstance(thread.get('messages'),list) and len(thread['messages'])<=24,'Invalid conversation.')
        require(type(thread.get('closed')) is bool and all(type(thread.get(k)) is int and thread[k]>=0 for k in ('created','updated','revision','unread_owner','unread_user')),'Invalid support metadata.')
        for item in thread['messages']:
            require(isinstance(item,dict) and type(item.get('t')) is int and type(item.get('owner')) is bool and isinstance(item.get('sender'),str) and item['sender'].isdigit() and isinstance(item.get('body_enc'),str) and len(item['body_enc'])<=6000,'Invalid encrypted support message.')
    s['approvals']={} # Never revive authorization decisions from a backup.
    require(all(isinstance(s[k],dict) for k in fresh() if k!="schema"),"Invalid snapshot structure.")
    settings_validate(s["settings"])
    for a in s["apis"].values():
        if a.get("is_trial"):a.update(trial_invalidated=True,active=False)
        require(a.get("owner") in s["users"] and bool(re.fullmatch(r"[0-9a-f]{64}",a.get("key_hash",""))),"Invalid API in snapshot.")
    s["outbox"]={}; s["login_codes"]={}; s["sessions"]={}; s["challenges"]={}; s["system"].pop("backup_lease",None)
    s['settings']['campaigns_enabled']=False
    s['system'].update(log_verified='',log_disabled=False,backup_dispatch={},backup_requested=True)
    s['system'].pop('backup_id',None)
    for u in s['users'].values():u.pop('join_proof',None)
    for u in s['users'].values():u.update(updates_on=False,promo_pending='')
    for c in s['campaigns'].values():c.update(enabled=False,run=None)
    check_data_capacity(s)
    return s

def restore_blob(blob):
    restored=validate_restore(blob)
    require(not (restored['orders'] or restored['system'].get('external_payments')) and not (store.read()['orders'] or store.read()['system'].get('external_payments')),
        'Automatic restore is disabled once payment orders exist or balances have been adjusted. Reconcile financial records offline; never roll back settled payments.',409)
    run_backup(True)  # safety snapshot before destructive replacement
    def change(s):
        require(not (s['orders'] or s['system'].get('external_payments')),'A payment/order arrived during restore preparation. Restore blocked.',409)
        restored["trial_claims"]={**restored.get("trial_claims",{}),**s.get("trial_claims",{})}
        restored["starter_claims"]={**restored.get("starter_claims",{}),**s.get("starter_claims",{})};restored["approvals"]={}
        for uid,u in s['users'].items():
            if u.get('broadcast_hold') and uid in restored['users']:
                restored['users'][uid].update(updates_on=False,broadcast_hold=True)
        check_data_capacity(restored)
        audit(restored,"superadmin","backup.restore","Recovery codes and API keys are not re-issued.")
        s.clear(); s.update(restored)
    store.tx(change)

@app.post("/manage/backup")
@protected(superonly=True,elevated=True)
def backup_route(uid):
    result=run_backup(True); drain(1); return jsonify(result)
@app.get("/manage/export")
@protected(superonly=True,elevated=True)
def export_route(uid): return send_file(io.BytesIO(backup_blob()),mimetype="application/octet-stream",as_attachment=True,download_name="srdark-"+utc_day()+".enc")
@app.post("/manage/restore")
@protected(superonly=True,elevated=True)
def restore_route(uid):
    require(request.form.get("confirm")=="RESTORE","Type RESTORE to confirm.")
    file=request.files.get("file"); require(file is not None,"Choose an encrypted backup.")
    restore_blob(file.read()); session.clear(); return jsonify(message="Restored. Log in again.")

@app.route("/tasks/tick",methods=["GET","POST"])
def tick():
    require(store is not None and not DEMO,"Scheduler unavailable.",503)
    auth=request.headers.get("Authorization","")
    require(hmac.compare_digest(auth,"Bearer "+str(cfg("CRON_SECRET"))),"Invalid scheduler secret.",403)
    store.tx(operational_tick)
    engagement=store.tx(engagement_tick)
    sent=drain(8); result=run_backup(); sent+=drain(1)
    store.tx(lambda s:(prune_security_state(s),s["system"].update(last_tick=now())))
    return jsonify(ok=True,sent=sent,backup=result,engagement=engagement)

@app.post("/login")
def login_route():
    require(store is not None,"Finish setup first.",503); check_csrf()
    token=str(body().get("code","")); require(20<=len(token)<=80,"Invalid login code.",401)
    # Per-client failure cap is supplementary; login codes carry 192 bits of entropy.
    ip=digest(client_address())[:24]
    def exchange(s):
        limits=s["login_limits"]
        for k in list(limits):
            if limits[k]["until"]<now(): del limits[k]
        if ip not in limits and len(limits)>=4096: return None
        v=limits.setdefault(ip,{"n":0,"until":now()+600})
        if v["n"]>=20: return None
        v["n"]+=1; entry=s["login_codes"].pop(digest(token),None)
        if not entry or entry["expires"]<now(): return None
        require_web_admin(s,entry["uid"]); audit(s,entry["uid"],"web.login")
        if session.get("sid"): s["sessions"].pop(digest(session["sid"]),None)
        return entry["uid"],issue_web_session(s,entry["uid"],elevated=v415_enabled(s))
    result=store.tx(exchange); require(result is not None,"Invalid/expired code, or too many attempts. Request /panel again.",401)
    uid,sid=result; adopt_session(uid,sid)
    return jsonify(ok=True)

@app.post("/demo-login")
def demo_login():
    require(DEMO,"Not found.",404); check_csrf()
    require(body().get("role","admin")=="admin","The HTML demo is admin-only. User functions are in Telegram.",403,"ADMIN_WEB_ONLY")
    uid="10001"
    def enter(state):
        if session.get("sid"): state["sessions"].pop(digest(session["sid"]),None)
        return issue_web_session(state,uid)
    sid=store.tx(enter); adopt_session(uid,sid); return jsonify(ok=True)

@app.get("/")
def index():
    if session.get('uid'):
        try:
            require(store is not None,'Setup incomplete.',503)
            state=store.read();record=check_web_session(state,session['uid']);check_firebase_session(session['uid'],record)
            require(session.get('login_at',0)+28800>now(),'Session expired.',401)
        except Problem:session.clear()
    session.setdefault("csrf",secrets.token_hex(24))
    return render_template_string(PAGE,csrf=session["csrf"],logged=bool(session.get("uid")),demo=DEMO,setup=SETUP_ERROR,bot=bot_username(),nonce=getattr(g,"csp_nonce",""),firebase_web_key=str(cfg("FIREBASE_WEB_API_KEY") or ""),firebase_public=firebase_public_config(),firebase_ready=bool(firebase_login_available() and (FB_SUPER_UIDS or FB_ADMIN_UIDS) and not DEMO))

# UI is embedded below: no templates, JS bundles, CDN fonts or build step required.
PAGE = r'''<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="theme-color" content="#0b0e13"><title>SR DARK — API Console</title>
<style>
:root{color-scheme:dark;--bg:#0b0e13;--sidebar:#0e1117;--card:#11161e;--raised:#181e29;--line:#242c39;--text:#e9eef5;--muted:#8893a6;--blue:#6e99ff;--green:#79deb8;--red:#f39191;--radius:13px}*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font:14px/1.5 Inter,ui-sans-serif,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}button,input,select,textarea{font:inherit}button,a,input,select,textarea{outline-offset:4px}button{cursor:pointer}button:disabled{opacity:.45;cursor:wait}a{color:var(--blue);text-decoration:none}button svg,nav svg{width:18px;height:18px;flex:none}button{display:inline-flex;align-items:center;justify-content:center;gap:8px;border:1px solid var(--line);border-radius:8px;padding:9px 14px;background:var(--raised);color:var(--text);font-size:13px;font-weight:550;transition:.15s}button:hover{border-color:#4d607d;background:#222c3b}button.primary{background:#719bff;border-color:#719bff;color:#0b1731}button.primary:hover{background:#91b1ff}button.good{background:#15382e;border-color:#255943;color:#8be8bf}button.danger{color:#f69b9b;background:#291b23;border-color:#54303a}button.ghost{background:transparent}.small{font-size:12px;padding:6px 10px}.muted{color:var(--muted)}.mono,code{font-family:ui-monospace,SFMono-Regular,Consolas,monospace;font-size:12px}.hidden{display:none!important}.app{display:grid;grid-template-columns:224px minmax(0,1fr);min-height:100vh}.side{position:sticky;top:0;height:100vh;padding:28px 15px 17px;background:var(--sidebar);border-right:1px solid var(--line);display:flex;flex-direction:column}.brand{display:flex;align-items:center;gap:11px;padding:0 12px;font-size:17px;font-weight:780;letter-spacing:1px}.brand-mark{background:var(--blue);width:31px;height:34px;color:#0c1730;display:grid;place-items:center;font-size:22px;font-weight:900;clip-path:polygon(20% 0,100% 0,80% 100%,0 100%)}.edition{margin:13px 12px 28px;font-size:11px;color:var(--muted);letter-spacing:1.8px}.navlabel{color:#606d82;font-size:10px;letter-spacing:1.4px;margin:24px 13px 8px}nav button{background:none;border:0;width:100%;justify-content:flex-start;color:#949fb0;margin:3px 0;padding:10px 13px;gap:13px;border-radius:8px;font-size:13px}nav button.active{background:#1c2942;color:#a6bfff}nav button:hover{background:#1a202c}.sidebottom{margin-top:auto;padding:20px 10px 0;border-top:1px solid var(--line)}.avatar{border:1px solid #3b4961;background:#233049;border-radius:9px;width:34px;height:34px;display:grid;place-items:center;color:#b7c9e9;flex-shrink:0}.userbox{display:flex;align-items:center;gap:10px}.userbox strong{font-size:12px}.userbox span{font-size:10px;letter-spacing:.6px}.main{min-width:0}.topbar{height:76px;border-bottom:1px solid var(--line);display:flex;align-items:center;justify-content:space-between;padding:0 36px;gap:12px}.crumb{color:var(--muted);font-size:12px;display:flex;gap:12px;align-items:center}.crumb b{color:#d2dbe9;font-weight:450}.dot{display:inline-block;width:6px;height:6px;background:var(--green);border-radius:50%;margin-right:7px}.topright{display:flex;align-items:center;gap:15px;font-size:11px}.container{max-width:1440px;margin:0 auto;padding:30px 36px 36px}.demo{padding:8px 16px;background:#131e32;border:1px solid #293e61;border-radius:8px;color:#9ab6e9;font-size:11px;margin-bottom:26px;display:flex;align-items:center;justify-content:space-between;gap:12px}.pagehead{display:flex;align-items:center;justify-content:space-between;margin-bottom:27px;gap:14px}.eyebrow{text-transform:uppercase;letter-spacing:1.7px;font-size:10px;color:var(--blue);margin-bottom:7px}h1{font-size:27px;font-weight:620;letter-spacing:-.9px;margin:0 0 6px}h2{font-size:15px;margin:0;font-weight:580}h3{font-size:14px;margin:0 0 12px}.pagehead p{color:var(--muted);margin:0;font-size:12px}.actions{display:flex;align-items:center;gap:8px;flex-wrap:wrap}.cards{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:15px;margin-bottom:23px}.card{background:var(--card);border:1px solid var(--line);border-radius:var(--radius);padding:21px;min-width:0}.metrichead{display:flex;align-items:center;justify-content:space-between;color:var(--muted);font-size:11px}.metrichead svg{width:17px;height:17px;color:#788aa6}.metricvalue{font-size:29px;font-weight:550;letter-spacing:-1px;line-height:1.25;margin:17px 0 9px}.metricsub{font-size:10px;color:var(--muted)}.green{color:var(--green)}.blue{color:var(--blue)}.two{display:grid;grid-template-columns:minmax(0,1.7fr) minmax(275px,1fr);gap:20px;margin-bottom:23px}.cardhead{display:flex;align-items:center;justify-content:space-between;gap:10px;margin-bottom:20px}.tag{display:inline-flex;align-items:center;border-radius:5px;padding:3px 7px;background:#20302b;color:#8bdbb9;font-size:10px;letter-spacing:.1px;white-space:nowrap}.tag.blue{background:#1b2945;color:#a0bafe}.tag.gray{background:#242b36;color:#a5b0c0}.tag.red{background:#35232b;color:#f0a1a1}.chart{height:150px;position:relative;margin-top:17px}.chart svg{width:100%;height:100%;overflow:visible}.chartlabels{display:flex;justify-content:space-between;margin:12px 0 0;font-size:9px;color:#69778b}.chartnote{color:var(--muted);font-size:10px}.refcard{background:radial-gradient(ellipse at 100% 0%,#1e2e48 0%,transparent 65%),var(--card);display:flex;flex-direction:column}.refcard h2{font-size:19px;letter-spacing:-.4px;margin:10px 0}.refcard p{font-size:12px;color:var(--muted);margin:0 0 18px}.creditdots{display:flex;gap:6px;margin:2px 0 10px}.creditdots i{height:5px;flex:1;border-radius:3px;background:#303a4a}.creditdots i.filled{background:#84a7f8}.refdetails{display:flex;justify-content:space-between;font-size:10px;color:#a4b2c8;margin-bottom:18px}.refcard button{margin-top:auto;align-self:flex-start}.section{background:var(--card);border:1px solid var(--line);border-radius:var(--radius);margin-bottom:22px;overflow:hidden}.sectionheader{padding:20px 22px;display:flex;align-items:center;justify-content:space-between;gap:12px}.count{color:#78869c;font-size:11px;margin-left:9px}.tablewrap{overflow:auto}table{width:100%;border-collapse:collapse;white-space:nowrap}th{text-align:left;font-size:9px;font-weight:500;letter-spacing:.9px;text-transform:uppercase;color:#77869c;padding:12px 22px;background:#0f141c;border-top:1px solid var(--line);border-bottom:1px solid var(--line)}td{padding:16px 22px;font-size:12px;border-bottom:1px solid #202735}tr:last-child td{border-bottom:none}tbody tr:hover{background:#141c27}td strong{font-weight:550}td .sub{display:block;margin-top:4px;color:#728198;font-size:10px}.apiname{display:flex;align-items:center;gap:12px}.apiicon{border:1px solid #2d3b54;border-radius:8px;background:#182336;padding:9px;color:#87a7dd;display:flex}.apiicon svg{width:17px;height:17px}.usage{width:90px;height:3px;background:#2c3545;border-radius:3px;margin-top:7px;overflow:hidden}.usage i{height:100%;display:block;background:#7597db}.empty{padding:42px 24px;text-align:center;color:var(--muted);font-size:13px}.bottomgrid{display:grid;grid-template-columns:1fr 1fr;gap:20px}.activityitem{display:flex;gap:13px;align-items:center;padding:12px 0;border-bottom:1px solid #202735}.activityitem:last-child{border:0}.activityicon{height:29px;width:29px;border:1px solid #2d3a48;border-radius:7px;color:#819abb;display:grid;place-items:center}.activityicon svg{width:14px;height:14px}.activityitem strong{display:block;font-size:11px;font-weight:500}.activityitem small{color:var(--muted);font-size:10px}.activityitem time{font-size:10px;color:#64738a;margin-left:auto;white-space:nowrap}.callcode{background:#0b1018;border:1px solid var(--line);border-radius:8px;padding:17px;color:#96b6ee;white-space:pre-wrap;word-break:break-word;line-height:1.9;font-size:11px}.caption{font-size:11px;color:var(--muted)}.statusrow{display:flex;align-items:center;justify-content:space-between;margin:12px 0;padding-bottom:12px;border-bottom:1px solid var(--line);font-size:12px}.toolbar{display:flex;gap:8px;padding:0 22px 18px}.toolbar input{max-width:300px}.footer{display:flex;justify-content:space-between;font-size:10px;color:#5d6a7f;padding:4px 1px}.footer b{font-weight:500;color:#8c9bb1}.mobilemenu{display:none}.grid2{display:grid;grid-template-columns:1fr 1fr;gap:16px}.stack{display:flex;flex-direction:column;gap:15px}.field{display:flex;flex-direction:column;gap:7px;margin-bottom:15px}.field label{font-size:11px;color:#a7b2c3}.field small{color:var(--muted);font-size:10px}input,select,textarea{border:1px solid #303b4d;background:#0e141e;color:var(--text);border-radius:7px;padding:10px 12px;width:100%;font-size:12px}textarea{resize:vertical;min-height:100px;font-family:ui-monospace,monospace}input:focus,select:focus,textarea:focus{outline:1px solid var(--blue);border-color:var(--blue)}input[type=checkbox]{width:auto;accent-color:var(--blue)}.checklabel{display:flex;align-items:center;gap:10px;font-size:12px}.notice{background:#182338;border:1px solid #2a4263;border-radius:8px;padding:13px 15px;font-size:12px;color:#abc2e4;margin-bottom:17px}.notice.warn{color:#d2b78e;background:#282219;border-color:#4a3c29}.cataloggrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:17px}.cataloggrid .card p{color:var(--muted);font-size:12px;min-height:40px}.chip{display:inline-flex;padding:5px 9px;color:#a2badf;background:#1c2941;border-radius:6px;font-size:10px}.tablebutton{background:none;border:0;color:#96aecd;padding:7px}.wide{width:100%}.buttonrow{display:flex;justify-content:flex-end;gap:8px;margin-top:20px}.bigcoins{font-size:56px;letter-spacing:-3px;line-height:1.2;margin:15px 0}.login{min-height:100vh;display:grid;grid-template-columns:1.1fr 1fr;max-width:1400px;margin:auto}.loginleft{padding:64px 70px;background:radial-gradient(ellipse at 20% 30%,#15243b 0%,transparent 65%);display:flex;flex-direction:column;justify-content:space-between}.loginleft h1{font-size:51px;line-height:1.14;letter-spacing:-2px;max-width:440px;margin:25px 0}.loginleft p{font-size:15px;color:var(--muted);max-width:360px}.loginright{display:flex;align-items:center;justify-content:center;padding:40px;border-left:1px solid var(--line)}.loginbox{width:100%;max-width:360px}.loginbox h2{font-size:23px;letter-spacing:-.6px;margin-bottom:8px}.loginbox p{font-size:13px;color:var(--muted);margin-bottom:26px}.loginbox .field{margin-top:24px}.loginsteps{display:flex;gap:18px;align-items:center;margin-top:24px;font-size:11px;color:#91a0b5}.loginsteps span{color:#7b9bdd}.loginerror{font-size:12px;color:var(--red);min-height:24px;margin-top:12px}.divider{border-top:1px solid var(--line);margin:23px 0}.modalback{position:fixed;inset:0;background:#030711bd;backdrop-filter:blur(5px);display:flex;align-items:center;justify-content:center;z-index:200;padding:20px}.modal{width:100%;max-width:620px;max-height:88vh;overflow-y:auto;background:#121925;border:1px solid #34415a;border-radius:15px;padding:25px;box-shadow:0 25px 100px #0009}.modalheader{display:flex;justify-content:space-between;align-items:center;margin-bottom:21px}.modalheader h2{font-size:19px}.modalerror{color:var(--red);font-size:12px}.modal pre{white-space:pre-wrap;word-break:break-word}.toastbox{position:fixed;bottom:23px;right:23px;z-index:300;display:flex;flex-direction:column;gap:9px}.toast{border:1px solid #47618a;background:#1b2940;color:#dbe7fa;border-radius:9px;padding:13px 18px;max-width:390px;box-shadow:0 8px 30px #0008;font-size:12px}.toast.bad{border-color:#8a4e5b;color:#ffbfc7}.loading{padding:100px;text-align:center;color:var(--muted)}.settingsform{max-width:880px}.settingsform .card{margin-bottom:18px}details summary{cursor:pointer;color:#9db9e9;font-size:12px}details pre{font-size:11px;white-space:pre-wrap;word-break:break-word}
@media(min-width:1500px){.container{padding-top:38px}.cards{gap:20px}.card{padding:24px}}@media(max-width:1100px){.app{grid-template-columns:190px minmax(0,1fr)}.container{padding:25px}.topbar{padding:0 25px}.cards{grid-template-columns:repeat(2,1fr)}.two{grid-template-columns:1fr}.chart{height:170px}.refcard p{max-width:480px}.refcard button{margin-top:10px}.bottomgrid{grid-template-columns:1fr}.loginleft{padding:45px}.loginleft h1{font-size:40px}}@media(max-width:700px){.app{grid-template-columns:1fr}.side{display:none;position:fixed;z-index:100;width:225px;box-shadow:20px 0 70px #000d}.side.open{display:flex}.mobilemenu{display:inline-flex;padding:6px}.topbar{height:60px;padding:0 18px}.container{padding:23px 16px}.topright .status{display:none}.cards{gap:10px}.card{padding:17px}.metricvalue{font-size:25px}.pagehead{align-items:flex-start;flex-direction:column;gap:18px}h1{font-size:24px}.grid2{grid-template-columns:1fr}.login{display:block}.loginleft{padding:28px}.loginleft h1{font-size:30px;margin-top:38px}.loginleft p,.loginleft footer{display:none}.loginright{padding:30px 25px;border-left:0}.loginleft .edition{margin-bottom:0}.two{gap:15px}.footer{gap:12px}.demo{align-items:flex-start}.demo .small{font-size:10px}td,th{padding-left:16px;padding-right:16px}.modal{padding:19px}.modalback{padding:12px}.crumb{font-size:11px}}
.side{overflow-y:auto}
</style></head><body>
{% if not logged %}
<div class="login"><section class="loginleft"><div><div class="brand"><span class="brand-mark">S</span>SR DARK</div><div class="edition">API INFRASTRUCTURE / 04</div></div><div><div class="eyebrow">One workspace. Every endpoint.</div><h1>Build APIs.<br>Grow your<br><span style="color:#81a9ff">possibilities.</span></h1><p>Your APIs, referral programme and Telegram community. Connected in one secure console.</p></div><footer class="caption">Built by DROID · Python edition</footer></section><section class="loginright"><div class="loginbox"><div class="eyebrow">Developer console</div><h2>Admin sign in.</h2><p>Admin-only console. Use your approved Firebase account or an authorized Telegram admin code. Users get trials, API URLs and management in the Telegram bot.</p><form id="firebaseloginform"><div class="field"><label for="fbemail">Firebase admin email</label><input id="fbemail" type="email" autocomplete="username" placeholder="admin@example.com" required></div><div class="field"><label for="fbpassword">Password</label><input id="fbpassword" type="password" autocomplete="current-password" required></div><button class="primary wide" type="submit" {% if not firebase_web_key or not firebase_ready or demo %}disabled{% endif %}>Login with Firebase</button><p class="caption">{% if demo %}Demo uses sample accounts; real Firebase login is disabled here.{% elif not firebase_web_key or not firebase_ready %}Server owner: configure the Web API key, dedicated backend Auth credentials, UID-restricted database rules and approved human admin UIDs first.{% else %}Only server-approved UIDs can enter the admin panel. No public admin signup.{% endif %}</p><div id="firebaseerror" class="loginerror"></div></form><div class="divider"></div><h3>Telegram admin login</h3>{% if setup %}<div class="notice warn"><b>Server setup required</b><br>{{setup}}<br><br>Edit CONFIG in main.py or set environment variables. Server secrets are configured privately, never in this page.</div>{% endif %}{% if bot %}<a href="https://t.me/{{bot}}?start=panel" target="_blank" rel="noopener" class="wide"><button class="primary wide" type="button">Open Telegram → send /panel</button></a>{% else %}<div class="notice">Register the webhook first. The server will verify the token and discover your bot username automatically.</div>{% endif %}<form id="loginform"><div class="field"><label for="logincode">One-time login code</label><input id="logincode" autocomplete="one-time-code" placeholder="Paste your code from /panel" required><small>Admins only. Private, single-use and valid for 5 minutes.</small></div><button class="wide" type="submit">Continue to console <span>→</span></button></form><div id="loginerror" class="loginerror"></div>{% if demo %}<div class="divider"></div><div class="notice">Interactive demo · sample database<br>No Telegram or cloud services connected.</div><div class="actions"><button class="primary" id="demoadmin">Explore admin demo</button></div>{% endif %}<p class="caption">Not an admin? <a href="https://t.me/{{bot}}?start=trial" target="_blank" rel="noopener">Open the user bot → free trial / APIs</a></p><div class="loginsteps"><span>01</span> Open bot <span>02</span> Get code <span>03</span> Build</div></div></section></div>
{% else %}
<div class="app"><aside class="side" id="sidebar"><div class="brand"><span class="brand-mark">S</span>SR DARK</div><div class="edition">DEVELOPER CONSOLE</div><nav id="navigation"></nav><div class="sidebottom"><div id="profile" class="userbox"></div><div style="display:flex;justify-content:space-between;align-items:center;margin-top:18px"><span class="caption" id="versionbadge">SR DARK</span><button class="ghost small" data-action="logout" title="Log out">↗</button></div></div></aside><main class="main"><header class="topbar"><div class="crumb"><button class="mobilemenu ghost" id="menubtn">☰</button>Workspace <span>/</span> <b id="breadcrumb">Overview</b></div><div class="topright"><span class="status muted"><i class="dot"></i><span id="storagebadge">Server storage</span></span><button class="ghost small" data-action="opennotifications" id="notificationbtn">Notifications</button><button class="ghost small" data-action="refresh" id="refreshbtn">Refresh</button></div></header><div class="container">{% if demo %}<div class="demo"><span><b>DEMO WORKSPACE</b> &nbsp; Explore with sample data. Telegram and cloud delivery are disabled.</span></div>{% endif %}<div id="content"><div class="loading">Loading your workspace…</div></div><footer class="footer"><span>SR DARK / <b>API infrastructure, simplified.</b></span><span id="synctime">Python backend · v4.10</span></footer></div></main></div>
{% endif %}
<div id="modalback" class="modalback hidden"><div class="modal" role="dialog" aria-modal="true" aria-labelledby="modaltitle"><div class="modalheader"><h2 id="modaltitle"></h2><button class="ghost small" data-action="closemodal" aria-label="Close dialog">✕</button></div><div id="modalbody"></div></div></div><div class="toastbox" id="toasts" role="status"></div>
<script nonce="{{nonce}}">
const CSRF={{csrf|tojson}}, ISDEMO={{demo|tojson}}, LOGGED={{logged|tojson}}, FB_WEB_KEY={{firebase_web_key|tojson}}, FB_PUBLIC_CONFIG={{firebase_public|tojson}};
let S=null, view='overview', modalSubmit=null, lastFocus=null;
const $=s=>document.querySelector(s), esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const fmt=n=>new Intl.NumberFormat('en-IN').format(n||0), date=t=>new Date(t*1000).toLocaleDateString('en-GB',{day:'2-digit',month:'short',year:'numeric'}), time=t=>new Date(t*1000).toLocaleTimeString('en-GB',{hour:'2-digit',minute:'2-digit'});
const icons={grid:'M3 3h7v7H3z M14 3h7v7h-7z M3 14h7v7H3z M14 14h7v7h-7z',api:'m8 5-6 7 6 7 M16 5l6 7-6 7 M14 3l-4 18',users:'M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2 M17 3a4 4 0 0 1 0 8 M22 21v-2a4 4 0 0 0-3-3.87 M13 7a4 4 0 1 1-8 0 4 4 0 0 1 8 0',chart:'M3 3v18h18 M7 14l4-4 4 3 6-8',gift:'M3 8h18v4H3z M5 12v9h14v-9 M12 8v13 M12 8S4 8 6 3c2-3 6 5 6 5s8 0 6-5c-2-3-6 5-6 5',storage:'M4 4h16v6H4z M4 14h16v6H4z M7 7h.01 M7 17h.01',clock:'M12 8v5l3 2 M22 12a10 10 0 1 1-20 0 10 10 0 0 1 20 0',settings:'M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8 M12 2v3 M12 19v3 M2 12h3 M19 12h3 M5 5l2 2 M17 17l2 2 M5 19l2-2 M17 7l2-2',cloud:'M6 18a5 5 0 1 1 0-10 7 7 0 0 1 13-1 5 5 0 0 1-1 11 M12 12v9 m-3-3 3 3 3-3',book:'M3 3h6a4 4 0 0 1 3 2 4 4 0 0 1 3-2h6v17h-6a4 4 0 0 0-3 2 4 4 0 0 0-3-2H3z M12 5v17',plus:'M12 5v14 M5 12h14',arrow:'M5 12h14 m-5-5 5 5-5 5',copy:'M9 9h12v12H9z M15 9V3H3v12h6',check:'m4 12 5 5L20 6',shield:'m12 2 9 4v6c0 5-9 10-9 10S3 17 3 12V6z M8 12l3 3 5-6'};
function icon(n){return `<svg fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" viewBox="0 0 24 24" aria-hidden="true"><path d="${icons[n]||icons.api}"/></svg>`}
function toast(text,bad=false){const e=document.createElement('div');e.className='toast'+(bad?' bad':'');e.textContent=text;$('#toasts').append(e);setTimeout(()=>e.remove(),5500)}
async function req(url,data,method,approvalId='',rawResponse=false){const options={method:method||(data?'POST':'GET'),headers:{'X-CSRF-Token':CSRF}};if(approvalId)options.headers['X-Owner-Approval']=approvalId;if(data instanceof FormData)options.body=data;else if(data){options.headers['Content-Type']='application/json';options.body=JSON.stringify(data)}const r=await fetch(url,options);if(r.ok&&rawResponse)return r;let j;try{j=await r.json()}catch{throw new Error('Server returned a non-JSON response. Check deployment.')}if(!r.ok){if(r.status===428&&j.error==='OWNER_APPROVAL_REQUIRED'&&!approvalId){toast('Approval sent to the owner bot. Keep this page open; this exact action resumes once approved.');for(let n=0;n<200;n++){await new Promise(resolve=>setTimeout(resolve,3000));const status=await req('/manage/approvals/'+j.approval_id);if(status.status==='approved')return req(url,data,method,j.approval_id,rawResponse);if(['rejected','expired','failed','completed','cancelled','executing'].includes(status.status))throw new Error('Owner request: '+status.status+'. No automatic replay.');}throw new Error('Approval timed out. No automatic replay.');}const err=new Error(j.message||'Request failed');err.code=j.error;throw err}return j}
async function firebasePasswordToken(email,password){if(!FB_WEB_KEY)throw new Error('Configure the Firebase Web API key on the server first.');const r=await fetch('https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key='+encodeURIComponent(FB_WEB_KEY),{method:'POST',headers:{'Content-Type':'application/json'},referrerPolicy:'origin',body:JSON.stringify({email,password,returnSecureToken:true})});const j=await r.json();if(!r.ok||!j.idToken)throw new Error('Firebase login failed. Check email/password and enable Email/Password sign-in in Firebase.');return j.idToken}
async function copy(text){try{await navigator.clipboard.writeText(text);toast('Copied to clipboard.')}catch{modal('Copy value',`<textarea readonly>${esc(text)}</textarea>`)} }
function isAdmin(){return ['admin','superadmin'].includes(S.me.role)}function isSuper(){return S.me.role==='superadmin'}
function nav(){let items=[['overview','grid','Overview'],['analytics','chart','Daily statistics'],['apis','api',isAdmin()?'Endpoints':'My APIs'],['catalog','book','API catalogue'],['referrals','gift',isAdmin()?'Referral review':'Referrals'],['engagement','users',isAdmin()?'Welcome & Broadcast':'Updates'],['wallet','gift','Wallet & Buy'],['developer','book','Developer'],['security','shield','Security centre']];if(isAdmin())items.push(['notifications','clock','Notifications'],['users','users','Users & roles'],['storage','storage','JSON storage'],['activity','clock','Activity log']);if(isSuper())items.push(['operations','settings','Operations'],['backups','cloud','Backups'],['settings','settings','Settings']);items.push(['docs','shield','Help & docs']);$('#navigation').innerHTML=items.map((i,n)=>(i[0]==='users'?'<div class="navlabel">ADMINISTRATION</div>':'')+`<button data-view="${i[0]}" class="${view===i[0]?'active':''}">${icon(i[1])}${i[2]}</button>`).join('');$('#profile').innerHTML=`<div class="avatar">${esc(S.me.name.slice(0,1))}</div><div><strong>${esc(S.me.name)}</strong><br><span class="muted">${esc(S.me.role.toUpperCase())}</span></div>`;if($('#versionbadge'))$('#versionbadge').textContent='v'+S.version+' · DROID';if($('#notificationbtn'))$('#notificationbtn').textContent='Notifications · '+(S.notifications||[]).filter(n=>!(S.notification_seen_ids||[]).includes(n.id)).length;$('#storagebadge').textContent=ISDEMO?'Local demo':S.storage==='firebase'?'Firebase RTDB':'SQLite storage';$('#breadcrumb').textContent=items.find(i=>i[0]===view)?.[2]||'Overview'}
async function refresh(){S=await req('/manage/state');nav();render();$('#synctime').textContent='Last synced '+new Date().toLocaleTimeString('en-GB',{hour:'2-digit',minute:'2-digit'});}
function head(kicker,title,desc,action=''){return `<div class="pagehead"><div><div class="eyebrow">${kicker}</div><h1>${title}</h1><p>${desc}</p></div><div class="actions">${action}</div></div>`}
function button(action,text,primary=false,id=''){return `<button data-action="${action}" ${id?`data-id="${esc(id)}"`:''} class="${primary?'primary':''}">${text}</button>`}
function metric(label,value,sub,ico){return `<div class="card"><div class="metrichead">${label}${icon(ico)}</div><div class="metricvalue">${value}</div><div class="metricsub">${sub}</div></div>`}
function status(a){return `<span class="tag ${a.status==='active'?'':['expired','exhausted'].includes(a.status)?'red':'gray'}">${a.status==='active'?'● Active':a.status==='expired'?'Expired':a.status==='exhausted'?'Trial used':'Paused'}</span>`}
function apiTable(list){if(!list.length)return '<div class="empty">No APIs yet. Create your first endpoint to get started.</div>';return `<div class="tablewrap"><table><thead><tr><th>Endpoint</th><th>Status</th><th>Usage</th><th>Expires</th><th></th></tr></thead><tbody>${list.map(a=>`<tr><td><div class="apiname"><span class="apiicon">${icon('api')}</span><div><strong>${esc(a.name)}</strong><span class="sub mono">${esc(a.id)}</span></div></div></td><td>${status(a)}</td><td>${fmt(a.is_trial?a.calls:a.used)} <span class="muted">/ ${fmt(a.is_trial?a.trial_limit:a.daily)} ${a.is_trial?'total trial':'today'}</span><div class="usage"><i style="width:${Math.min(100,(a.is_trial?a.calls/a.trial_limit:a.used/a.daily)*100)}%"></i></div></td><td>${date(a.expires)}<span class="sub">${esc(a.mode)} · ${a.rpm}/min</span></td><td><button data-action="apiedit" data-id="${esc(a.id)}" class="small ghost">Manage ${icon('arrow')}</button></td></tr>`).join('')}</tbody></table></div>`}
function activities(logs){return logs.length?logs.slice(0,4).map(l=>`<div class="activityitem"><span class="activityicon">${icon(l.event.includes('api')?'api':'shield')}</span><div><strong>${esc(l.event.replaceAll('.',' / '))}</strong><small>${esc(l.actor)}${l.detail?' · '+esc(l.detail.slice(0,45)):''}</small></div><time>${time(l.t)}</time></div>`).join(''):'<p class="caption">Your audit events will appear here.</p>'}
function chart(){const bins=Array(12).fill(0);for(const a of S.apis)for(const h of a.history||[]){const age=Math.floor((Date.now()/1000-h.t)/300);if(age>=0&&age<12)bins[11-age]++}const max=Math.max(1,...bins),pts=bins.map((n,i)=>`${i*50},${120-n/max*96}`),line=pts.join(' ');return `<div class="chart"><svg viewBox="0 0 550 130" preserveAspectRatio="none"><defs><linearGradient id="chartFill" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stop-color="#79deb8" stop-opacity=".20"/><stop offset="1" stop-color="#79deb8" stop-opacity="0"/></linearGradient></defs>${[24,56,88,120].map(y=>`<line x1="0" x2="550" y1="${y}" y2="${y}" stroke="#26313d" stroke-dasharray="3 5"/>`).join('')}<polygon points="0,130 ${line} 550,130" fill="url(#chartFill)"/><polyline points="${line}" fill="none" stroke="#80dcb7" stroke-width="2.2" vector-effect="non-scaling-stroke"/></svg></div><div class="chartlabels"><span>60 min ago</span><span>45 min</span><span>30 min</span><span>15 min</span><span>Now</span></div>`}
function adminOverview(){const enabled=S.catalog.filter(c=>c.enabled!==false),trials=enabled.filter(c=>c.trial_enabled),calls=S.apis.reduce((n,a)=>n+a.calls,0),hosts=S.settings.allowed_hosts||[],logs=!!(S.operations?.log_channel&&S.system?.log_verified===S.operations.log_channel&&!S.system?.log_disabled);return head('SR DARK / Admin console','Your sources. Customer-ready APIs.','Add an authorized source to the catalogue. Customers choose, preview and buy from Telegram.',button('newcatalog',icon('plus')+' Add source for customers',true)+(isSuper()?' '+button('rewardtools','Rewards & credits'):''))+`<div class="cards">${metric('ENABLED SOURCES',fmt(enabled.length),'Categories available in the bot','book')}${metric('WORKSPACE ENDPOINTS',fmt(S.apis.length),'Customer and admin test endpoints','api')}${metric('REGISTERED ACCOUNTS',fmt(S.users.length),'Manage roles and balances','users')}${metric('ACCEPTED REQUESTS',fmt(calls),'Lifetime usage','chart')}</div><div class="two"><div class="card refcard"><span class="eyebrow">SET UP → PREVIEW → SELL</span><h2>One source. Personal customer keys.</h2><div class="statusrow"><span>01 · Add source in API catalogue</span><span class="tag blue">Admin</span></div><div class="statusrow"><span>02 · Set price and synthetic sample</span><span class="tag blue">Admin</span></div><div class="statusrow"><span>03 · Choose → preview → buy</span><span class="tag">Telegram</span></div><p class="caption">Customers receive your Render URL and their personal key—not the upstream provider key. Admin test endpoints are free; customer purchases use the configured price.</p><div class="actions">${button('opencatalog','View sources',true)}${button('create','Create admin test endpoint')}</div></div><div class="card"><h2>Setup checklist</h2><div class="statusrow"><span>Trial-enabled sources</span><b>${trials.length}</b></div><div class="statusrow"><span>Approved proxy hostnames</span><b>${hosts.length}</b></div><div class="statusrow"><span>Private logs</span><b>${logs?'Verified':'Needs owner review'}</b></div><div class="statusrow"><span>Background scheduler</span><b>${S.system?.last_tick?'Last run '+time(S.system.last_tick):'Not recorded'}</b></div>${!hosts.length?'<p class="caption">No proxy hosts approved. Static JSON and offline validators still work without an upstream host.</p>':''}<div class="actions">${isSuper()?button('openhostsettings','Review allowed hosts')+' '+button('openoperations','Logs & permissions'):''}${button('opendocs','Setup help')}</div></div></div><div class="section"><div class="sectionheader"><h2>Workspace endpoints <span class="count">${S.apis.length}</span></h2><button class="ghost small" data-view="apis">View all ${icon('arrow')}</button></div>${apiTable(S.apis.slice(0,4))}</div><div class="two"><div class="card"><h2>Recent activity</h2>${activities(S.logs.slice(0,6))}</div><div class="card"><h2>Test the customer experience</h2><p>Open the bot and send <code>/buyapi</code>. Choose a catalogue category, inspect its sample, then confirm.</p><p class="caption">Use an ordinary test customer to check coin deduction. A source-host error is a missing approval—not an invitation to turn off source security.</p>${S.bot_username?`<a href="https://t.me/${esc(S.bot_username)}?start" target="_blank" rel="noopener">Open customer bot ↗</a>`:''}</div></div>`}
document.addEventListener('input',e=>{if(['f_url','f_param'].includes(e.target.id))sourceHostHint()});
function previewSource(id){const c=S.catalog.find(x=>x.id===id);if(!c)return;const has=Object.prototype.hasOwnProperty.call(c,'demo_response')||c.mode==='static',sample=Object.prototype.hasOwnProperty.call(c,'demo_response')?c.demo_response:c.data,raw=has?JSON.stringify({ok:true,data:sample},null,2):'';modal('Customer sample preview',`<div class="notice">Saved synthetic illustration only. No upstream call, purchase or quota use. Usage/expiry metadata is omitted.</div><h3>${esc(c.name)}</h3>${has?`<pre class="callcode">${esc(raw.slice(0,2000))}</pre>${raw.length>2000?'<p class="caption">Preview truncated. Save a smaller synthetic sample for the customer bot.</p>':''}`:'<p>No sample saved. Edit this source and add Demo response JSON.</p>'}`)}
function sourceHostHint(){const box=$('#sourcehosthint');if(!box)return;const mode=$('#f_mode')?.value;if(mode!=='proxy'){box.classList.add('hidden');return}box.classList.remove('hidden');try{const raw=$('#f_url')?.value||'',u=new URL(raw.replace(/&(?:amp;)+/g,'&')),host=u.hostname.toLowerCase(),allowed=(S.settings.allowed_hosts||[]).includes(host),param=$('#f_param')?.value||'value',candidates=[...u.searchParams].filter(([k,v])=>!v&&!['key','api_key','apikey','token','access_token','secret'].includes(k.toLowerCase())&&/^[A-Za-z][A-Za-z0-9_]{0,30}$/.test(k));box.className='notice '+(allowed?'':'warn');box.innerHTML='<b>'+esc(host)+'</b><br>'+(allowed?'Host is approved. Confirm the provider input parameter and your right to supply this data.':'Host is not approved. Owner: Settings → Allowed proxy hosts. Approve only an exact trusted hostname after reviewing the source. Saving a URL never grants approval.')+(candidates.length===1&&candidates[0][0]!==param?'<br><br>Parameter mismatch: the URL has an empty <b>'+esc(candidates[0][0])+'</b> parameter; this form currently uses <b>'+esc(param)+'</b>. Match the provider documentation.':'')+(raw.includes('&amp;')?'<br>HTML &amp;amp; separators will be normalized to &amp; when saved.':'')}catch(e){box.className='notice';box.textContent='Enter a valid HTTPS source URL. Only its hostname—not the URL or key—belongs in the allowlist.'}}
function overview(){if(isAdmin())return adminOverview();const active=S.apis.filter(a=>a.status==='active').length,calls=S.apis.reduce((n,a)=>n+a.calls,0),coins=S.me.coins,cost=S.settings.default_api_price;return head('Your workspace','A little control. Endless possibilities.','Manage your endpoints, track usage and build what comes next.',button('create',icon('plus')+' Create API',true))+(!S.me.active?`<div class="notice">Activate your account to start creating APIs. ${button('activate','Activate account',true)}</div>`:'')+`<div class="cards">${metric('TOTAL ENDPOINTS',fmt(S.apis.length),`<span class="green">${active} active</span> · ${S.apis.length-active} inactive`,'api')}${metric('TOTAL REQUESTS',fmt(calls),'Lifetime accepted attempts','chart')}${metric(isAdmin()?'REGISTERED USERS':'QUALIFIED REFERRALS',fmt(isAdmin()?S.users.length:S.me.refs),isAdmin()?'Telegram-linked accounts':'One reward per new account','users')}${metric('COIN BALANCE',fmt(coins),`${cost} coins unlock an API`,'gift')}</div><div class="two"><div class="card"><div class="cardhead"><div><h2>Request activity</h2><span class="chartnote">Recent sample · up to 30 calls per endpoint</span></div><span class="tag gray">Last hour</span></div>${chart()}</div><div class="card refcard"><span class="eyebrow">Build together</span><h2>Your network. Your next API.</h2><p>Earn ${cost} coins (${Math.ceil(cost/S.settings.referral_reward)} approved referrals at the current rate), or purchase a pack. Unlock an endpoint with ${S.settings.daily_limit} daily requests for ${S.settings.valid_days} days.</p><div class="creditdots">${Array.from({length:Math.min(cost,20)},(_,i)=>`<i class="${i<Math.min(cost,coins)?'filled':''}"></i>`).join('')}</div><div class="refdetails"><span>${coins} available coins</span><span>${Math.max(0,cost-coins)} to next API</span></div>${button('copyref',icon('copy')+' Copy invite link')}</div></div><div class="section"><div class="sectionheader"><h2>${isAdmin()?'Workspace':'Your'} endpoints <span class="count">${S.apis.length}</span></h2><button class="ghost small" data-view="apis">View all ${icon('arrow')}</button></div>${apiTable(S.apis.slice(0,4))}</div><div class="bottomgrid"><div class="card"><div class="cardhead"><h2>${isAdmin()?'Latest activity':'Your plan'}</h2><span class="tag gray">${isAdmin()?'Audit trail':'Referral access'}</span></div>${isAdmin()?activities(S.logs):`<div class="statusrow"><span>Daily requests</span><b>${S.settings.daily_limit}</b></div><div class="statusrow"><span>API validity</span><b>${S.settings.valid_days} days</b></div><p class="caption">Paid plan limits reset at 00:00 UTC; trials never reset or renew.</p>`}</div><div class="card"><div class="cardhead"><h2>Your first request</h2><span class="tag blue">GET</span></div><pre class="callcode">curl '${esc(location.origin)}/api/API_ID' \\\n  -H 'X-API-Key: YOUR_API_KEY'</pre><p class="caption">Real JSON responses. No browser tab required.<br>Keep API keys out of URLs, screenshots and public repositories.</p></div></div>`}
function apis(){return head('API workspace','Your endpoints','Create, edit, renew and monitor APIs. Keys are displayed only once.',button('create',icon('plus')+' Create API',true))+`<div class="section"><div class="sectionheader"><h2>${isAdmin()?'All workspace APIs':'My APIs'} <span class="count">${S.apis.length}</span></h2><span class="caption">Paid: daily reset · Trials: no reset</span></div><div class="toolbar"><input id="apisearch" placeholder="Search name or ID…" aria-label="Search APIs"></div><div id="apitable">${apiTable(S.apis)}</div></div>`}

function catalog(){return head('Source library','API catalogue','Admin-managed sources. Your own key, expiry and daily quota.',isAdmin()?button('newcatalog',icon('plus')+' Add source',true)+' '+button('newdemosource','Add demo JSON source'):'')+`<div class="cataloggrid">${S.catalog.map(c=>`<div class="card"><div class="cardhead"><span class="apiicon">${icon('book')}</span><span class="tag ${c.enabled===false?'red':'blue'}">${c.enabled===false?'Disabled':esc(c.mode)}</span></div><h2>${esc(c.name)}</h2><p>${c.plans?.length?c.plans.map(p=>`${esc(p.name)}: ${p.price} coins · ${p.days}d · ${p.daily}/day · ${p.rpm}/min${p.total?' · '+p.total+' total':''}${p.enabled===false?' (disabled)':''}`).join('<br>'):`${S.settings.daily_limit} requests/day · ${S.settings.valid_days} days<br>${esc(priceText(c))} per personal endpoint<br>${esc(c.referral_hint||'')}`}<br><code>${esc(c.id)}</code>${['proxy','validation'].includes(c.mode)?'<br>Example: <code>'+esc(c.param)+'='+esc(c.example_value||'Not set')+'</code>':''}</p><div class="actions">${button('previewsource','Sample response',false,c.id)}${button('fromcatalog',isAdmin()?'Create test endpoint':'Create my API',true,c.id)}${c.trial_enabled?'<span class="tag blue">Trial enabled · claim in bot</span>':''}${isAdmin()?button('editcatalog','Edit',false,c.id):''}</div></div>`).join('')||'<div class="empty">No approved sources yet. An admin can add one here.</div>'}</div>`}
function referrals(){if(S.me.auth_provider==='firebase')return head('Administrator workspace','Share your bot.','Referral coins belong to Telegram users. Firebase admins manage the catalogue and do not need coins.')+`<div class="card"><p class="caption">Create a catalogue source, set its public example input, then share this bot link with users.</p><pre class="callcode">${esc(S.referral_url)}</pre>${button('copyref','Copy bot link',true)}</div>`;return `<div class="notice">Both earn coins: you receive ${S.settings.referral_reward}; your genuinely new referred friend receives ${S.settings.referral_new_user_reward}. All configured joins + activation are required${S.settings.referral_approval?', then admin approval':''}. Default API: ${Math.ceil(S.settings.default_api_price/S.settings.referral_reward)} referrals from zero, or ${Math.ceil(Math.max(0,S.settings.default_api_price-S.me.coins)/S.settings.referral_reward)} more with your current balance.</div>`+head('Community rewards','Good APIs deserve good company.','Invite new users. Earn coins after activation and any required admin approval.')+`<div class="two"><div class="card refcard"><div class="eyebrow">Your balance</div><div class="bigcoins">${fmt(S.me.coins)} <span style="font-size:16px;letter-spacing:0;color:#9aaac3">coins</span></div><p>1 approved referral = ${S.settings.referral_reward} coins. Default API: ${S.settings.default_api_price} coins · ${S.settings.daily_limit} requests/day · ${S.settings.valid_days} days</p><div class="field"><label>Your invite link</label><input value="${esc(S.referral_url)}" readonly></div>${button('copyref',icon('copy')+' Copy referral link',true)}</div><div class="card"><h2>How it works</h2><div class="statusrow"><span>01 &nbsp; Share your personal link</span></div><div class="statusrow"><span>02 &nbsp; New user activates their account</span></div><div class="statusrow"><span>03 &nbsp; Collect ${S.settings.default_api_price} coins and create an API</span></div><p class="caption">${S.settings.referral_approval?'Admin approval is required before credit is awarded.':'Coins are awarded automatically on first activation.'} Duplicate IDs and self-referrals do not count. Multiple accounts controlled by one person cannot reliably be detected; admins can switch on manual review.</p></div></div><div class="section"><div class="sectionheader"><h2>${isAdmin()?'Referral review':'Your referrals'}</h2></div><div class="tablewrap"><table><thead><tr><th>Invited user</th><th>Referrer</th><th>Date</th><th>Status</th><th></th></tr></thead><tbody>${S.referrals.map(r=>`<tr><td class="mono">${esc(r.to)}</td><td class="mono">${esc(r.from)}</td><td>${date(r.t)}</td><td><span class="tag ${r.status==='pending'?'blue':r.status==='rejected'?'red':''}">${esc(r.status)}</span></td><td>${isAdmin()&&r.status==='pending'?`<button class="small good" data-action="approveref" data-id="${esc(r.id)}">Approve</button> <button class="small danger" data-action="rejectref" data-id="${esc(r.id)}">Reject</button>`:''}</td></tr>`).join('')||'<tr><td colspan="5" class="empty">No referrals yet.</td></tr>'}</tbody></table></div></div>`}
function users(){return head('People & access','The people behind your platform.','Telegram/Firebase accounts, roles and wallet balances. Super-admins come from server config.')+`<div class="section"><div class="sectionheader"><h2>Members <span class="count">${S.users.length}</span></h2></div><div class="toolbar"><input id="usersearch" placeholder="Search user or Telegram ID…" aria-label="Search users"></div><div class="tablewrap"><table><thead><tr><th>Member</th><th>Role</th><th>Coins</th><th>Status</th><th>Joined</th><th></th></tr></thead><tbody id="usertable">${userRows(S.users)}</tbody></table></div></div>`}
function userRows(list){return list.map(u=>`<tr><td><strong>${esc(u.name)}</strong><span class="sub mono">${esc(u.id)}</span></td><td><span class="tag ${u.role==='superadmin'?'blue':'gray'}">${esc(u.role)}</span></td><td>${u.coins}</td><td><span class="tag ${u.blocked?'red':!u.active?'gray':''}">${u.blocked?'Blocked':u.active?'Active':'Not activated'}</span></td><td>${date(u.joined)}</td><td>${u.role==='superadmin'||u.auth_provider==='firebase'?'<span class="caption">Config-managed</span>':button('edituser','Manage',false,u.id)}</td></tr>`).join('')}
function storage(){return head('Structured data','JSON storage','Private server-side key/value records. API callers cannot read this storage.',button('newkv',icon('plus')+' Add record',true))+`<div class="section"><div class="tablewrap"><table><thead><tr><th>Key</th><th>Value preview</th><th></th></tr></thead><tbody>${Object.entries(S.kv).map(([k,v])=>`<tr><td class="mono">${esc(k)}</td><td class="mono">${esc(JSON.stringify(v).slice(0,100))}</td><td>${button('editkv','Edit',false,k)}</td></tr>`).join('')||'<tr><td class="empty">No records yet.</td></tr>'}</tbody></table></div></div>`}
function activity(){return head('Accountability by design','Activity log','A bounded audit trail of the latest 400 events. Showing the newest 150.')+`<div class="section"><div class="tablewrap"><table><thead><tr><th>Time</th><th>Actor</th><th>Event</th><th>Detail</th></tr></thead><tbody>${S.logs.map(l=>`<tr><td>${date(l.t)} · ${time(l.t)}</td><td class="mono">${esc(l.actor)}</td><td><span class="tag gray">${esc(l.event)}</span></td><td>${esc(l.detail)}</td></tr>`).join('')}</tbody></table></div></div>`}
function backups(){return head('Recovery & continuity','A safety net for your workspace.','Encrypted snapshots, cloud storage and private Telegram delivery.',button('backup',icon('cloud')+' Back up now',true))+`<div class="cards">${metric('BACKUP INTERVAL',S.settings.backup_hours+'h','Embedded worker or scheduler','clock')}${metric('RETENTION',S.settings.backup_keep,'Snapshots per destination','storage')}${metric('LAST SAVED',S.system.last_backup?time(S.system.last_backup):'Not yet',S.system.last_backup?date(S.system.last_backup):'Run your first backup','cloud')}${metric('OUTBOX',S.pending,'Pending Telegram deliveries','users')}</div>${S.system.backup_warning?`<div class="notice warn">${esc(S.system.backup_warning)}</div>`:''}${S.system.backup_delivery_warning?`<div class="notice warn">${esc(S.system.backup_delivery_warning)}</div>`:''}<div class="notice">Encrypted Telegram files: ${esc(S.settings.backup_delivery)} · Last acknowledged file: ${S.system.last_backup_delivered?date(S.system.last_backup_delivered.at)+' '+time(S.system.last_backup_delivered.at):'Not delivered yet'}. Backup creation and Telegram delivery are separate statuses.</div><div class="grid2"><div class="card"><h2>Snapshot destinations</h2><div class="statusrow"><span>Primary database</span><b>${esc(S.storage)}</b></div><div class="statusrow"><span>Last backup destinations</span><span>${esc((S.system.backup_locations||[]).join(', ')||'Not configured / no run')}</span></div><div class="statusrow"><span>Scheduler heartbeat</span><span>${S.system.last_tick?date(S.system.last_tick)+' '+time(S.system.last_tick):'No tick received'}</span></div><p class="caption">Firebase snapshots stay in the same project. For independent cloud recovery, configure S3/R2. SQLite backups need a persistent disk or S3/R2; ephemeral hosting is not a backup.</p>${button('export',icon('cloud')+' Download encrypted snapshot')}</div><div class="card"><h2>Restore a snapshot</h2><p class="caption">Destructive operation: replaces all v4 users, APIs, coins and settings. A safety snapshot is taken first. Keep the encryption key from your original server.</p><form id="restoreform"><div class="field"><label>Encrypted .enc file</label><input type="file" name="file" accept=".enc" required></div><div class="field"><label>Type RESTORE to confirm</label><input name="confirm" placeholder="RESTORE" required></div><button type="submit" class="danger">Restore workspace</button></form><p class="caption">Old HTML v3 exports are not compatible. Do not upload those here.</p></div></div>`}
const field=(name,label,value,type='text',hint='')=>`<div class="field"><label for="f_${name}">${label}</label><input id="f_${name}" name="${name}" type="${type}" value="${esc(value)}" ${type==='number'?'min="0"':''}>${hint?`<small>${hint}</small>`:''}</div>`;
const area=(name,label,value,hint='')=>`<div class="field"><label for="f_${name}">${label}</label><textarea id="f_${name}" name="${name}" spellcheck="false">${esc(typeof value==='string'?value:JSON.stringify(value,null,2))}</textarea>${hint?`<small>${hint}</small>`:''}</div>`;
function promoLinkFields(prefix,links=[]){return `<p class="caption">Up to four HTTPS link buttons. For your other bots, use https://t.me/YourBot. Leave both fields blank to omit a button. Never put private API keys in promotional links.</p>`+Array.from({length:4},(_,i)=>`<div class="grid2">${field(prefix+'_label_'+i,'Button '+(i+1)+' label',links[i]?.label||'')}${field(prefix+'_url_'+i,'Button '+(i+1)+' HTTPS URL',links[i]?.url||'','url')}</div>`).join('')}
function readPromoLinks(f,prefix){const links=[];for(let i=0;i<4;i++){const label=f.elements[prefix+'_label_'+i].value.trim(),url=f.elements[prefix+'_url_'+i].value.trim();if(label||url){if(!label||!url)throw new Error('Each button needs both a label and a URL.');links.push({label,url})}}return links}
function engagement(){const e=S.engagement,c=e.config;return head('Welcome & retention','Welcome well. Message thoughtfully.','Set the photo welcome, promote your bots and run scheduled campaigns. Engagement is not guaranteed.',button('newcampaign',icon('plus')+' Add campaign',true)+' '+button('dailybroadcast','Daily broadcast template'))+`<div class="cards">${metric('BROADCAST AUDIENCE',fmt(e.subscribers),'Started bot · not blocked or excluded','users')}${metric('ACTIVE IN 7 DAYS',fmt(e.active_7d),'Bot interaction / accepted API attempt','chart')}${metric('CAMPAIGN QUEUE',e.queued,'Up to 100 optional messages pending','clock')}${metric('SCHEDULER',e.last_tick?time(e.last_tick):'Not run',e.last_tick?date(e.last_tick):'Configure /tasks/tick every minute','settings')}</div>${ISDEMO?'<div class="notice">Demo: no Telegram delivery and no live scheduled jobs. You can configure and inspect campaigns, but a real bot/cron is required to send.</div>':''}<div class="notice ${c.campaigns_enabled?'':'warn'}">Campaign master switch: <b>${c.campaigns_enabled?'ON':'OFF'}</b>. New users are enrolled after /start. Blocked accounts and previous disabled-message preferences are excluded. Quiet hours and global per-user caps apply across all campaigns. Users can stop delivery by blocking this bot in Telegram. Already in-flight messages cannot be recalled.</div><div class="two"><div class="card"><h2>Select your welcome image in Telegram</h2><p>1. Use a registered Telegram admin account.<br>2. Send <code>/setwelcome</code> to this bot in a private chat.<br>3. Send the selected photo within 10 minutes (not as a document). Its optional caption becomes the welcome text.<br>4. Use <b>Send welcome preview</b> below to preview the media. Repeated /start reuses the existing menu screen.</p><p class="caption">Firebase-only owner? Configure your numeric Telegram ID in SUPER_ADMIN_IDS, restart, and send /start first. The image stays on Telegram; no bot token or image-download URL is exposed in this panel.</p><div class="actions">${button('copywelcomecmd','Copy /setwelcome')}${S.bot_username?`<a href="https://t.me/${esc(S.bot_username)}" target="_blank" rel="noopener">Open bot ↗</a>`:''}</div><p><span class="tag ${c.welcome_photo?'blue':'gray'}">${c.welcome_photo?'Photo selected':'No photo yet · text welcome'}</span></p>${c.welcome_photo?`<details><summary>Saved Telegram photo ID</summary><p class="caption" style="overflow-wrap:anywhere">${esc(c.welcome_photo)}</p></details>`:''}</div><div class="card"><h2>Test before broadcasting</h2><div class="field"><label for="promo_preview_target">Registered Telegram admin</label><select id="promo_preview_target">${e.preview_targets.map(t=>`<option value="${esc(t.id)}">${esc(t.name)} · ${esc(t.id)}</option>`).join('')||'<option value="">No eligible Telegram admin yet</option>'}</select></div>${button('welcomepreview','Send welcome preview',true)}<p class="caption">Previews go only to registered private-chat admins, never to the subscriber list. One preview every 30 seconds per admin. Fresh security confirmation is required. Preview delivery bypasses campaign quiet hours because you explicitly requested it.</p><p class="caption">Last scheduler scan: ${e.last_tick?date(e.last_tick)+' '+time(e.last_tick):'Not recorded'}. The browser does not run the scheduler. Random times are due-times, not guaranteed delivery times. Acknowledged counts mean Telegram accepted a send, not that a user read it.</p></div></div><form id="engagementform" class="settingsform"><div class="card"><h2>Welcome caption & link buttons</h2><label class="checklabel"><input name="welcome_dashboard" type="checkbox" ${c.welcome_dashboard?'checked':''}> Dynamic dashboard: real name, ID, coins, referrals, active APIs and status</label><p class="caption">When enabled, the dashboard replaces the custom caption below. /dashboard also removes the separate sticker. Upload an original video with /setvideo; screenshot references cannot be animated.</p>${c.welcome_video?'<label class="checklabel"><input name="remove_video" type="checkbox"> Remove saved welcome video</label>':''}${formatSelect("welcome_mode",c.welcome_mode)}<p class="caption">Use /setmessage in Telegram to capture a formatted welcome, or /setwelcomemd for Markdown. The text box below edits plain/Markdown content; captured entities must be updated through Telegram.</p><div class="field"><label for="welcome_caption">Welcome message · plain text</label><textarea id="welcome_caption" name="welcome_caption" rows="5" maxlength="700">${esc(c.welcome_caption)}</textarea><small>Placeholders: {name}, {coins}, {diamonds}, {referral_reward}, {api_price}. Text is safely escaped for Telegram. Keep it under 700 text units; emojis may count as two.</small></div>${promoLinkFields('welcome',c.welcome_links)}${c.welcome_photo?'<label class="checklabel"><input name="remove_photo" type="checkbox"> Remove selected image and use text-only welcome</label>':''}</div><div class="card"><h2>Delivery policy · applies to all campaigns</h2><label class="checklabel"><input name="campaigns_enabled" type="checkbox" ${c.campaigns_enabled?'checked':''}> Enable optional campaign scheduling</label><div class="grid2">${field('campaign_timezone','IANA timezone',c.campaign_timezone,'text','Default Asia/Kolkata. Same-day delivery window only.')}${field('delivery_start_hour','Start hour (0–23)',c.delivery_start_hour,'number')}${field('delivery_end_hour','End hour (1–24, exclusive)',c.delivery_end_hour,'number')}${field('campaign_daily_cap','Maximum messages/user/day (1–3)',c.campaign_daily_cap,'number')}${field('campaign_gap_hours','Minimum gap in hours (6–168)',c.campaign_gap_hours,'number')}</div><p class="caption">Default: 10:00–20:00 India time, one optional message per user/day, 24-hour minimum gap. Daily schedules respect quiet hours and shared caps. Turning the master switch off cancels queued campaigns; payment/security replies are unaffected.</p><button class="primary" type="submit">Save welcome & delivery policy</button></div></form><div class="section"><div class="sectionheader"><h2>Your campaigns · ${e.campaigns.length}/12</h2>${button('refresh','Refresh status')}</div><div class="cataloggrid" style="padding:0 20px 20px">${e.campaigns.map(c=>`<div class="card"><div class="cardhead"><span class="tag ${c.enabled?'blue':'gray'}">${c.enabled?'Enabled':'Paused'}</span><span class="caption">${esc(c.trigger)}</span></div><h3>${esc(c.name)}</h3><p class="caption"><code>${esc(c.id)}</code></p><p class="caption">${c.trigger==='once'?'One-time broadcast':c.trigger==='random'?`${c.min_hours}–${c.max_hours}h randomized intervals`:c.trigger==='inactive'?`Inactive for at least ${c.threshold_days} days`:`API expires within ${c.threshold_days} days or expired within 24h`}</p><p style="white-space:pre-wrap;overflow-wrap:anywhere">${esc(c.text.slice(0,160))}${c.text.length>160?'…':''}</p><p class="caption">${c.sent} acknowledged · ${c.failed} failed · ${c.skipped} cancelled/stale<br>${c.completed&&c.trigger==='once'?'Scan complete; queued deliveries may remain':c.run?'Scan in progress':('Next due: '+date(c.next_at)+' '+time(c.next_at))}${c.last_error?'<br>'+esc(c.last_error):''}</p><div class="actions">${button('copycampaigncmd','Copy capture command',false,c.id)}${button('editcampaign','Edit',false,c.id)}${button('previewcampaign','Admin preview',false,c.id)}${button('togglecampaign',c.enabled?'Pause':'Enable',false,c.id)}${c.trigger==='once'&&c.completed?'':button('runcampaign','Queue run',true,c.id)}<button class="danger small" data-action="deletecampaign" data-id="${esc(c.id)}">Delete</button></div></div>`).join('')||'<div class="empty">No campaigns yet. Add a random-time promotion, inactivity reminder or API-expiry reminder. Set your other bots as HTTPS link buttons.</div>'}</div></div>`}
function campaignModal(id){const c=S.engagement.campaigns.find(c=>c.id===id)||{trigger:'random',min_hours:24,max_hours:24,threshold_days:3,links:[],enabled:false};modal(id?'Edit campaign':'Add campaign',`<form id="modalform">${field('name','Campaign name',c.name||'')}<div class="field"><label for="campaign_trigger">Trigger</label><select id="campaign_trigger" name="trigger"><option value="once" ${c.trigger==='once'?'selected':''}>One-time broadcast</option><option value="random" ${c.trigger==='random'?'selected':''}>Scheduled recurring promotion</option><option value="inactive" ${c.trigger==='inactive'?'selected':''}>Inactivity reminder</option><option value="expiry" ${c.trigger==='expiry'?'selected':''}>API expiry reminder</option></select></div><div id="campaign_interval" class="grid2">${field('min_hours','Minimum interval (6–168 hours)',c.min_hours,'number')}${field('max_hours','Maximum interval (up to 336 hours)',c.max_hours,'number')}</div><div id="campaign_threshold">${field('threshold_days','Threshold days (inactive: 1–90; expiry: 1–14)',c.threshold_days,'number')}</div>${formatSelect("text_mode",c.text_mode)}<p class="caption">Capture Telegram formatting with /setcampaign ${esc(c.id||"CAMPAIGN_ID")} after creating the campaign.</p><div class="field"><label for="campaign_text">Broadcast message</label><textarea id="campaign_text" name="text" rows="5" maxlength="700">${esc(c.text||'')}</textarea><small>Use {name}, {coins}, {diamonds}, {referral_reward}, {api_price}. Expiry reminders also support {api_name}, {expires}, {days_left}, {status}. Never include passwords, API keys or private personal data.</small></div>${promoLinkFields('campaign',c.links)}<label class="checklabel"><input name="use_welcome_photo" type="checkbox" ${c.use_welcome_photo?'checked':''}> Attach selected welcome image</label><br><label class="checklabel"><input name="enabled" type="checkbox" ${c.enabled?'checked':''}> Enable this campaign (master switch and cron also required)</label><p class="caption">Inactivity sends once per inactive episode. Expiry sends once per API/expiry value per campaign; renewal can qualify again. All campaigns share the user's bot-start eligibility, historical exclusions, daily cap and minimum gap.</p>${formEnd('Save campaign')}`,async f=>{const d={id,name:f.elements.name.value,text:f.elements.text.value,text_mode:f.elements.text_mode.value,trigger:f.elements.trigger.value,min_hours:+f.elements.min_hours.value,max_hours:+f.elements.max_hours.value,threshold_days:+f.elements.threshold_days.value,links:readPromoLinks(f,'campaign'),use_welcome_photo:f.elements.use_welcome_photo.checked,enabled:f.elements.enabled.checked};await req('/manage/campaigns',d);closeModal();await refresh();toast('Campaign saved.')});syncCampaignFields()}
function syncCampaignFields(){const trigger=$('#campaign_trigger')?.value;if(!trigger)return;$('#campaign_interval').classList.toggle('hidden',trigger!=='random');$('#campaign_threshold').classList.toggle('hidden',!['inactive','expiry'].includes(trigger))}

function priceText(a={}){return `${a.price??S.settings.default_api_price} ${a.billing_currency||'coins'}`}
function currencyField(value='coins'){return `<div class="field"><label for="f_billing_currency">API payment currency</label><select id="f_billing_currency" name="billing_currency"><option value="coins" ${value==='coins'?'selected':''}>Coins</option><option value="diamonds" ${value==='diamonds'?'selected':''}>Diamonds</option></select></div>`}
function wallet(){const st=S.settings,telegram=/^\d+$/.test(S.me.id);return head('Earn · buy · convert','Your wallet. Your choice.','Coins and diamonds are app balances, not Telegram Stars or cash. API prices are set per source.',button('refresh','Refresh balance'))+`<div class="cards">${metric('COINS',fmt(S.me.coins),`${st.referral_reward} per approved referral`,'gift')}${metric('DIAMONDS',fmt(S.me.diamonds),'Purchase packs · premium API access','api')}${metric('DIAMOND → COINS',st.diamond_coin_rate||'Not set','One-way conversion · admin-set rate','arrow')}${metric('DEFAULT API',st.default_api_price+' coins',`${st.daily_limit}/day · ${st.valid_days} days`,'chart')}</div>${S.me.wallet_hold?'<div class="notice warn">Wallet on hold after a refund. API access is paused while a balance is negative. Contact payment support to reconcile.</div>':''}${!S.me.active?'<div class="notice">Activate your account from Overview or /start before purchasing.</div>':''}<div class="two"><div class="card"><h2>Convert diamonds into coins</h2><p class="caption">Coins cannot be converted back into diamonds. The quoted rate is checked again before conversion.</p>${st.diamond_coin_rate?`<form id="conversionform">${field('convert_amount','Diamonds to convert',1,'number')}<button type="submit" class="primary">Review conversion</button></form>`:'<p class="caption">The owner has not configured conversion yet.</p>'}</div><div class="card"><h2>Payment & refund support</h2><p class="caption">Telegram purchases use Stars. On this standalone website, UPI purchases can be discussed privately with the owner and are credited only after bank verification.</p>${st.support_username?`<a class="tag blue" href="https://t.me/${esc(st.support_username)}" target="_blank" rel="noopener">Contact @${esc(st.support_username)}</a>`:'<div class="notice warn">Owner: configure a support username before enabling purchases.</div>'}<details><summary>Purchase terms</summary><p class="caption" style="white-space:pre-wrap">${esc(st.payment_terms)}</p></details></div></div><div class="section"><div class="sectionheader"><h2>Buy coins or diamonds</h2>${isSuper()?button('newpack','Add purchase pack',true):''}</div><div class="cataloggrid">${st.purchase_packs.filter(p=>isSuper()||p.enabled).map(p=>`<div class="card"><span class="tag ${p.enabled?'blue':'gray'}">${esc(p.currency)}${p.enabled?'':' · disabled'}</span><h2>${esc(p.name)}</h2><div class="metricvalue">${fmt(p.amount)} <span style="font-size:16px">${esc(p.currency)}</span></div><p>${p.stars} Telegram Stars${p.inr_paise?' · ₹'+(p.inr_paise/100).toFixed(2)+' manual UPI':''}</p><div class="actions">${telegram&&p.enabled?button('buystars','Buy with Stars',true,p.id):''}${telegram&&p.enabled&&p.inr_paise&&st.support_username?button('buyupi','UPI via DM',false,p.id):''}${isSuper()?button('editpack','Edit pack',false,p.id):''}</div></div>`).join('')||'<div class="empty">No purchase packs yet. The owner sets pack units and real Star/UPI prices; no exchange rate is assumed.</div>'}</div></div>${isSuper()?`<form id="economyform" class="settingsform"><div class="card"><h2>Wallet policy · owner only</h2><div class="grid2">${field('referral_reward','Coins per approved referral',st.referral_reward,'number')}${field('referral_new_user_reward','Referred new user reward · coins',st.referral_new_user_reward,'number')}${field('default_api_price','Default API price (coins)',st.default_api_price,'number')}${field('diamond_coin_rate','Coins per diamond (0 = disabled)',st.diamond_coin_rate,'number')}${field('support_username','Support / UPI DM Telegram username',st.support_username,'text','Username only, no @ needed. Check ownership before publishing.')}</div><div class="field"><label>Purchase and refund terms</label><textarea name="payment_terms" rows="4" maxlength="1500">${esc(st.payment_terms)}</textarea></div><p class="caption">Changing pack prices affects new orders only. Pending orders retain their quote. Catalogue prices are edited per source; existing API renewals retain their stored plan price.</p><button class="primary" type="submit">Save wallet policy</button></div></form>`:''}<div class="section"><div class="sectionheader"><h2>${isSuper()?'Payment review':'Your purchases'} · latest 100</h2></div><div class="tablewrap"><table><thead><tr><th>Order / user</th><th>Pack</th><th>Payment</th><th>Status</th><th>Action</th></tr></thead><tbody>${S.orders.map(o=>`<tr><td class="mono">${esc(o.id)}<span class="sub">${esc(o.uid)}</span></td><td>${o.amount} ${esc(o.currency)}<span class="sub">${esc(o.name)}</span></td><td>${o.method==='stars'?o.stars+' Stars':'₹'+(o.inr_paise/100).toFixed(2)}<span class="sub">${esc(o.reference||'')}</span></td><td><span class="tag ${o.status==='paid'?'':o.status==='pending'?'blue':'gray'}">${esc(o.status)}</span></td><td>${isSuper()&&o.method==='upi'&&o.status==='pending'?button('approvepayment','Verify & approve',false,o.id)+' '+button('rejectpayment','Reject',false,o.id):isSuper()&&o.method==='stars'&&['paid','refund_pending'].includes(o.status)?button('refundpayment',o.status==='paid'?'Refund Stars':'Retry / reconcile refund',false,o.id):'—'}</td></tr>`).join('')||'<tr><td colspan="5" class="empty">No purchases yet.</td></tr>'}</tbody></table></div></div><div class="section"><h2>Recent wallet activity · latest 100</h2><div class="tablewrap"><table><thead><tr><th>Time</th><th>Account</th><th>Change</th><th>Reason</th><th>Balance after</th></tr></thead><tbody>${S.ledger.map(t=>`<tr><td>${date(t.t)} ${time(t.t)}</td><td class="mono">${esc(t.uid)}</td><td>${t.delta>0?'+':''}${t.delta} ${esc(t.currency)}</td><td>${esc(t.reason)}<span class="sub">${esc(t.reference)}</span></td><td>${t.balance}</td></tr>`).join('')||'<tr><td colspan="5" class="empty">No wallet activity yet.</td></tr>'}</tbody></table></div></div>`}
function packModal(id){const p=S.settings.purchase_packs.find(p=>p.id===id)||{currency:'diamonds',enabled:true};modal(id?'Edit purchase pack':'Add purchase pack',`<form id="modalform"><div class="notice">Set your own prices. Telegram Stars are integer payment units, not an INR or diamond exchange rate.</div>${field('pack_id','Unique pack ID',p.id||'')}${field('name','Pack name',p.name||'')}<div class="field"><label>Wallet currency</label><select name="currency"><option value="coins" ${p.currency==='coins'?'selected':''}>Coins</option><option value="diamonds" ${p.currency==='diamonds'?'selected':''}>Diamonds</option></select></div><div class="grid2">${field('amount','Coins / diamonds credited',p.amount||'','number')}${field('stars','Telegram Stars charged',p.stars||'','number')}${field('inr','UPI price in INR (0 = disabled)',p.inr_paise?p.inr_paise/100:0,'number')}</div><label class="checklabel"><input name="enabled" type="checkbox" ${p.enabled?'checked':''}> Enabled</label>${formEnd('Save pack')}`,async f=>{const value={id:f.elements.pack_id.value.trim(),name:f.elements.name.value.trim(),currency:f.elements.currency.value,amount:+f.elements.amount.value,stars:+f.elements.stars.value,inr_paise:Math.round(+f.elements.inr.value*100),enabled:f.elements.enabled.checked};const packs=S.settings.purchase_packs.filter(x=>x.id!==id);if(packs.some(x=>x.id===value.id))throw new Error('Pack ID already exists.');packs.push(value);await req('/manage/admin/settings',{purchase_packs:packs});closeModal();await refresh();toast('Purchase pack saved.')});if(id)$('#f_pack_id').readOnly=true;$('#f_inr').step='0.01'}
function manualPurchase(id){const p=S.settings.purchase_packs.find(p=>p.id===id);modal('Manual UPI purchase',`<form id="modalform"><div class="notice warn">${p.amount} ${esc(p.currency)} · ₹${(p.inr_paise/100).toFixed(2)}. First contact the owner to confirm payment details. Never trust unsolicited DMs. A screenshot is not proof of settlement.</div><p><a href="https://t.me/${esc(S.settings.support_username)}" target="_blank" rel="noopener">Message @${esc(S.settings.support_username)}</a></p>${field('reference','Actual UPI payment reference / UTR','','text','After payment, submit the bank reference once. Owner verifies their bank account before crediting. Do not enter a password, Aadhaar number or API key.')}${formEnd('Submit for verification')}`,async f=>{const r=await req('/manage/wallet/manual',{pack_id:id,reference:f.elements.reference.value.trim(),quote:{currency:p.currency,amount:p.amount,inr_paise:p.inr_paise}});closeModal();await refresh();toast(r.message)})}
function developer(){const st=S.settings;return head('Developer & integrations','Build with the right query.','Every API source defines its own parameter name, example input and payment currency.')+`<div class="two"><div class="card"><span class="tag blue">Developer</span><h2>${esc(st.developer_name)}</h2><p style="white-space:pre-wrap">${esc(st.developer_about)}</p><div class="actions">${st.developer_website?`<a href="${esc(st.developer_website)}" target="_blank" rel="noopener">Developer website ↗</a>`:''}${st.developer_username?`<a href="https://t.me/${esc(st.developer_username)}" target="_blank" rel="noopener">@${esc(st.developer_username)}</a>`:''}</div></div><div class="card"><h2>Separate query per source</h2><p class="caption">An admin can configure <code>mobile</code>, <code>aadhaar</code>, <code>tg_id</code>, or another valid parameter name independently. The saved public example is inserted into the new user's full keyed URL.</p><p class="caption">Only use authorized sources and dummy/test examples. This platform does not supply private identity databases or authorize access to personal data.</p><p class="caption">Keys are shown only on creation/rotation. The examples below use YOUR_API_KEY; substitute your own endpoint ID and key privately.</p></div></div><div class="section"><div class="sectionheader"><h2>Source-specific request examples</h2></div><div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,420px),1fr));gap:16px;padding:0 20px 20px">${S.catalog.map(c=>{const q=c.mode==='proxy'?'?'+new URLSearchParams({[c.param]:c.example_value||'YOUR_INPUT'}):'',url=location.origin+'/api/YOUR_API_ID'+q;const curl='curl '+JSON.stringify(url)+' -H "X-API-Key: YOUR_API_KEY"',py='import requests\nresponse = requests.get('+JSON.stringify(url)+', headers={"X-API-Key": "YOUR_API_KEY"}, timeout=15)\nprint(response.json())',js='const response = await fetch('+JSON.stringify(url)+', {headers: {"X-API-Key": "YOUR_API_KEY"}});\nconsole.log(await response.json());';return `<div class="card"><h3>${esc(c.name)}</h3><span class="tag">${esc(priceText(c))}</span><p class="caption">${c.mode==='proxy'?'Query: <code>'+esc(c.param)+'</code><br>Saved example: <code>'+esc(c.example_value||'Not configured')+'</code>':'Static JSON · no input parameter'}</p><details open><summary>cURL</summary><pre class="callcode">${esc(curl)}</pre></details><details><summary>Python</summary><pre class="callcode">${esc(py)}</pre></details><details><summary>JavaScript</summary><pre class="callcode">${esc(js)}</pre><p class="caption">Use server-side JavaScript or same-origin code. Cross-origin browser authentication requires an appropriate CORS policy; private API keys must not be embedded in public websites.</p></details></div>`}).join('')||'<div class="empty">Add a catalogue source to publish its parameter and examples.</div>'}</div></div>${isSuper()?`<form id="developerform" class="card"><h2>Developer profile · owner settings</h2>${field('developer_name','Developer name',st.developer_name)}<div class="field"><label>About</label><textarea name="developer_about" rows="4" maxlength="1000">${esc(st.developer_about)}</textarea></div>${field('developer_website','HTTPS website',st.developer_website,'url')}${field('developer_username','Developer Telegram username',st.developer_username)}<button class="primary" type="submit">Save developer profile</button></form>`:''}`}

function settings(){let st=S.settings,f=S.firebase_connection||{};return head('Platform policy','Settings that work everywhere.','Super-admin only. New API plans use these defaults; response rules apply on every request.')+`<div class="card" style="margin-bottom:20px"><h3>Firebase Auth + Realtime Database</h3><p class="caption">Project: ${esc(f.project_id||'Not configured')} · Backend: ${esc(f.storage||S.storage)} · Namespace: ${esc(f.namespace||'srdark_v4')}</p><p class="caption">Access mode: ${esc(f.access_mode||'rest')}<br>Shared backend/admin account opt-in: ${f.shared_account_enabled?'Enabled — this account also has direct database access':'Disabled — separate identities'}<br>${f.access_mode==='sdk'?'Legacy service account configured: '+(f.service_account_configured?'Yes':'No'):'Dedicated backend Auth credentials configured: '+(f.backend_credentials_configured?'Yes':'No')}<br>Public web API key configured: ${f.web_key_configured?'Yes':'No'}<br>Approved Firebase admin UIDs configured: ${f.approved_admins_configured?'Yes':'No'}<br>Firebase login configuration ready: ${f.admin_login_configured?'Yes':'No'}</p><p class="caption">These are configuration checks, not proof of a successful real login/backup. Enable Firebase Authentication → Email/Password, create your admin account and approve its exact Auth UID in FIREBASE_SUPER_ADMIN_UIDS. REST mode needs no service-account JSON: privately fill the dedicated backend Auth email, password and UID in CONFIG; publish rules allowing only that UID on state/backups. Separate backend/admin accounts are recommended. Explicit FIREBASE_ALLOW_SHARED_ACCOUNT=true permits the same allowlisted UID for both, including direct database access. Never set public read/write or share the password. SDK mode retains its certificate option. No backend credentials are displayed or editable here. Telegram owner IDs are not Firebase Auth UIDs.</p></div><form id="settingsform" class="settingsform"><div class="card"><h3>One-time API trial</h3><label class="checklabel"><input name="trial_enabled" type="checkbox" ${st.trial_enabled?'checked':''}> Enable trial access</label><div class="grid2">${field('trial_minutes','Duration (1–1440 minutes)',st.trial_minutes,'number')}${field('trial_requests','TOTAL requests (1–10000)',st.trial_requests,'number')}${field('trial_rpm','Requests per minute (1–1000)',st.trial_rpm,'number')}</div><p class="caption">New claims use these limits. Existing trials keep their original deadline/budget. Disabling global or source trial access stops existing trial calls too. Each catalogue source requires separate trial opt-in. Trial keys always require authentication and cannot be renewed or extended.</p></div><div class="card"><h3>Referral & API defaults</h3><div class="grid2">${field('default_api_price','Default API price (coins)',st.default_api_price,'number')}${field('daily_limit','Requests per day',st.daily_limit,'number')}${field('valid_days','Validity in days',st.valid_days,'number')}${field('rpm','Requests per minute',st.rpm,'number')}${field('max_apis','Maximum APIs per user',st.max_apis,'number')}${field('max_payload_kb','Maximum JSON payload (KB)',st.max_payload_kb,'number')}</div><label class="checklabel"><input name="referral_approval" type="checkbox" ${st.referral_approval?'checked':''}> Require admin approval for future referral rewards</label><br><label class="checklabel"><input name="allow_custom" type="checkbox" ${st.allow_custom?'checked':''}> Allow users to create custom APIs</label><br><label class="checklabel"><input name="apply_existing" type="checkbox"> Apply daily/RPM defaults to legacy paid APIs only (purchased plans keep their limits)</label></div><div class="card"><h3>Starter access, keys & owner approvals</h3><label class="checklabel"><input name="modern_controls" type="checkbox" ${st.modern_controls?'checked':''}> Modern button navigation and guided controls</label><label class="checklabel"><input name="starter_enabled" type="checkbox" ${st.starter_enabled?'checked':''}> Enable a separate one-time free starter API</label><div class="grid2">${field('bot_user_rpm','Customer bot actions/minute',st.bot_user_rpm,'number')}${field('bot_admin_rpm','Admin bot actions/minute',st.bot_admin_rpm,'number')}${field('starter_days','Free starter days',st.starter_days,'number')}${field('starter_daily','Free starter requests/day',st.starter_daily,'number')}${field('starter_rpm','Free starter requests/minute',st.starter_rpm,'number')}${field('starter_extend_price','Coins for validity extension',st.starter_extend_price,'number')}${field('starter_extend_days','Days per extension purchase',st.starter_extend_days,'number')}${field('starter_quota_price','Coins for quota upgrade',st.starter_quota_price,'number')}${field('starter_quota_add','Daily quota added per upgrade',st.starter_quota_add,'number')}${field('custom_key_price','Coins for custom Droidx key',st.custom_key_price,'number')}${field('web_unlock_minutes','Sensitive unlock minutes · 5–120',st.web_unlock_minutes,'number')}</div><div class="field"><label>New key format · existing keys unchanged</label><select name="key_style"><option value="droid15" ${st.key_style==='droid15'?'selected':''}>Droid + 10 random letters (15 total)</option><option value="legacy" ${st.key_style==='legacy'?'selected':''}>Legacy long random key</option></select></div><label class="checklabel"><input name="safe_chat_receipts" type="checkbox" ${st.safe_chat_receipts?'checked':''}> Safe text in legacy-controls mode too (modern mode always uses safe text when TXT is off)</label><label class="checklabel"><input name="owner_approval_required" type="checkbox" ${st.owner_approval_required?'checked':''}> Require Telegram owner approval for sensitive web actions and subordinate broadcasts</label><p class="caption">Accounts get at most one free starter and one short demo. Referral coins use the existing wallet. Prices above are owner-configurable. Custom Droidx keys include the chosen label and a longer random secret, not a guessable name. Enable starter access for each source in API catalogue.</p><p class="caption">Owner identities are hosting-CONFIG-only, never editable here. Approvals are one-use and bound to the original session, path and payload. Normal API GET requests and purchases do not wait for approval. New header-only defaults never change existing endpoint clients.</p></div><div class="card"><h3>Private delivery & admin alerts</h3><label class="checklabel"><input name="api_receipts_txt" type="checkbox" ${st.api_receipts_txt?'checked':''}> Deliver new API keys as private TXT documents in Telegram</label><label class="checklabel"><input name="admin_event_notifications" type="checkbox" ${st.admin_event_notifications?'checked':''}> Queue key-free admin DM notifications for important events</label><label class="checklabel"><input name="default_header_only" type="checkbox" ${st.default_header_only?'checked':''}> New endpoints require header authentication (existing endpoints unchanged)</label><p class="caption">TXT avoids a chat link preview, but is still a secret file. For strict protection against pasted keyed URLs, use header-only. Customers then send X-API-Key or Bearer headers. Use the enabled embedded worker on always-on Render. Vercel needs your authenticated minute scheduler.</p></div><div class="card"><h3>Approved upstream hosts</h3>${area('allowed_hosts','Exact hostnames (JSON array)',st.allowed_hosts,'HTTPS only. No wildcards, redirects, local/private addresses or third-party relay services.')}</div><div class="card"><h3>Universal response rules</h3>${area('replace','String replacements',st.replace,'JSON pairs, e.g. [["old text", "new text"]]. Changes values inside data, never auth or quota metadata.')}${area('inject','Extra JSON fields',st.inject,'Object merged into the response data. Applies to all existing and new APIs.')}</div><div class="card"><h3>Error messages</h3>${field('error_expired','Expired API',st.error_expired)}${field('error_daily','Daily quota',st.error_daily)}${field('error_key','Invalid API key',st.error_key)}</div><div class="card"><h3>Backups</h3><div class="grid2">${field('backup_hours','Interval (hours)',st.backup_hours,'number')}${field('backup_keep','Retained snapshots',st.backup_keep,'number')}</div><div class="field"><label>Encrypted Telegram backup file destination</label><select name="backup_delivery"><option value="logs" ${st.backup_delivery==='logs'?'selected':''}>Verified private logs group</option><option value="owner" ${st.backup_delivery==='owner'?'selected':''}>Telegram owner DM</option><option value="both" ${st.backup_delivery==='both'?'selected':''}>Logs group + owner DM</option></select></div><p class="caption">Default: every 6 hours to verified private logs. The file is encrypted; the decryption key is never sent. Log privacy and bot permissions are checked again before each attachment. Use Operations → Verify private log destination first.</p><p class="caption">An enabled embedded worker handles scheduling on always-on Render. Otherwise call /tasks/tick regularly with an authenticated scheduler; this setting does not create a cloud cron job.</p></div><button class="primary" type="submit">${icon('check')} Save platform settings</button></form>`}
function docs(){return head('Designed to be clear','A small guide. A stronger platform.','Everything you need to operate this workspace responsibly.')+`<div class="grid2"><div class="card"><h3>Calling an API</h3><pre class="callcode">GET /api/API_ID?value=YOUR_INPUT\nX-API-Key: YOUR_API_KEY</pre><p class="caption">Static APIs do not need a parameter. Proxy APIs use their configured parameter. Keys are hashed on the server and shown only at creation/rotation. HTTP 401 = wrong key, 403 = paused/expired, 429 = quota exceeded.</p></div><div class="card"><h3>Quota & referrals</h3><p class="caption">The default API costs ${S.settings.default_api_price} coins; each approved referral earns ${S.settings.referral_reward} coins. A default API includes ${S.settings.daily_limit} requests/day for ${S.settings.valid_days} days. Creation spends the configured coins or diamonds; deletion does not refund them. Renewal extends validity and keeps today's usage.</p><p class="caption">Daily reset: 00:00 UTC / 05:30 IST. Accepted attempts consume quota even if the upstream fails. Invalid keys and missing parameters do not consume quota.</p></div><div class="card"><h3>Telegram controls</h3><pre class="callcode">/start · /create · /apis · /referral\n/panel · /admin · /backup · /cancel</pre><p class="caption">Users stay in the bot: /demo or /trial creates the one-time trial; /apis manages endpoints. The HTML panel, /panel and /confirm are admin-only. The bot runs through a webhook, not a browser tab. Native buttons use primary, success and danger styles; older Telegram clients may show uncoloured buttons. Admin-sensitive responses are private-chat only.</p></div><div class="card"><h3>Firebase admin & catalogue</h3><p class="caption">Login with your approved Firebase email/password. Confirm the same password in Security centre before sensitive changes. Add approved proxy hosts in Settings, then use API catalogue → Add source: choose HTTPS proxy, set URL, query parameter and a safe Public example value. The bot fills that example into each user’s full keyed URL automatically.</p><p class="caption">Examples are visible to users: never put credentials or private data in them. Firebase admin UIDs are approved only in private server config.</p></div><div class="card"><h3>Security & ownership</h3><p class="caption">Use only APIs and data you are authorized to access. Proxy hosts need super-admin approval. No public Firebase reads/writes; REST mode uses a dedicated backend Auth account and UID-scoped rules. API data stays nested so different records never become incorrectly mixed.</p><p class="caption">User → own API CRUD in Telegram only. Admin → HTML catalogue, users, referrals, API limits and JSON storage. Super-admin → role changes, coins, global settings and encrypted recovery.</p></div><div class="card"><h3>Operational checklist</h3><p class="caption">1. Configure HTTPS, bot and storage.<br>2. Register the Telegram webhook.<br>3. Schedule authenticated /tasks/tick requests.<br>4. Test a real backup and restore.<br>5. Set a host/WAF traffic limit.<br>6. Monitor scheduler heartbeat and delivery backlog.</p><p class="caption">Whole-state Firebase transactions are intended for small installations. High traffic needs a partitioned datastore and a dedicated job queue.</p></div><div class="card"><h3>Honest backup guarantees</h3><p class="caption">Fernet-encrypted snapshots can be stored in Firebase, persistent disk and optionally S3/R2. Encrypted files go to the selected verified private logs/owner destination; Firebase UIDs are not Telegram recipients. Back up the encryption key separately. A failed database read cannot produce a fresh snapshot; previous independent cloud backups remain available.</p><p class="caption">Telegram delivery is retried with an outbox. A crash after send but before acknowledgement can cause a duplicate message (at-least-once delivery).</p></div></div>`}
function security(){const sec=S.security;const firebaseConfirm=`<p class="caption">Confirm your Firebase admin password to unlock sensitive web actions for ${S.settings.web_unlock_minutes||5} minutes. Telegram /confirm is not needed for this account. This rotates your browser session and CSRF token.</p><p class="caption">${sec.elevated_until>Date.now()/1000?'Confirmed until '+time(sec.elevated_until):'Sensitive actions are locked.'}</p><form id="firebaseconfirmform"><div class="field"><label>Admin email</label><input type="email" name="email" value="${esc(S.me.email||'')}" readonly></div><div class="field"><label>Password</label><input type="password" name="password" autocomplete="current-password" required></div><button class="primary" type="submit">Confirm Firebase password</button></form>`;return head('Account & platform security','Your control centre.','Manage browser sessions and confirm sensitive actions. Edge protection requires separate hosting setup.')+(S.settings.owner_approval_required?'<div class="notice">Sensitive saves request approval in the configured owner bot DM. Approve the exact action; this browser resumes it once. Login and CSRF checks still apply. /panel or /planel provides a single-use admin login code.</div>':'')+`<div class="cards">${metric('SESSION PROTECTION','Server-side','Revocable · maximum 5 sessions','shield')}${metric('TRAFFIC GUARD',sec.admission.startsWith('Shared')?'Shared':'Local',esc(sec.admission),'chart')}${metric('EDGE / WAF','Not verified','Configure before production','cloud')}${metric('REFERRAL REVIEW',sec.referral_review?'Manual':'Automatic','Manual review reduces multi-account abuse','users')}</div><div class="notice warn">DDoS/WAF protection is not automatically provisioned. The app cannot verify that cloud-layer rules are active. No 100% attack-proof guarantee.</div>${isAdmin()?`<div class="card" style="margin-bottom:20px"><h2>Sensitive action confirmation</h2>${sec.confirmation_method==='firebase'?firebaseConfirm:`<p class="caption">Global settings, catalogue/storage changes, role/credit changes, other users’ APIs and backup/recovery need a fresh confirmation. In a private chat, send /confirm to your bot, then enter its 8-digit code here. This is a fresh Telegram confirmation, not an independent second factor. It unlocks sensitive web actions for ${S.settings.web_unlock_minutes||5} minutes and rotates your session token.</p>${ISDEMO?'<div class="notice">Demo bypasses Telegram confirmation. Production does not.</div>':`<p class="caption">${sec.elevated_until>Date.now()/1000?'Confirmed until '+time(sec.elevated_until):'Sensitive actions are locked.'}</p><form id="confirmform"><div class="field"><label for="confirmationcode">Telegram confirmation code</label><input id="confirmationcode" name="code" inputmode="numeric" pattern="[0-9]{8}" maxlength="8" autocomplete="one-time-code" required placeholder="8 digits from /confirm"></div><div class="actions"><a href="https://t.me/${esc(S.bot_username)}?start=confirm" target="_blank" rel="noopener">Open bot → /confirm</a><button class="primary" type="submit">Verify & unlock</button></div></form>`}`}</div>`:''}<div class="section"><div class="sectionheader"><h2>Active browser sessions</h2>${button('revokeothers','Sign out other devices')}</div><div class="tablewrap"><table><thead><tr><th>Device</th><th>Created</th><th>Expires</th><th></th></tr></thead><tbody>${sec.sessions.map(v=>`<tr><td><strong>${v.current?'This device':'Other device'}</strong><span class="sub">${esc(v.device.slice(0,65))}</span></td><td>${date(v.created)} ${time(v.created)}</td><td>${time(v.expires)}</td><td>${v.current?'<span class="tag">Current</span>':`<button class="small danger" data-action="revokesession" data-id="${esc(v.id)}">Sign out</button>`}</td></tr>`).join('')}</tbody></table></div></div><div class="card"><h3>Already enforced in the app</h3><p class="caption">Ownership checks · hashed API keys · encrypted backups · CSRF protection · script CSP · request limits · approved HTTPS sources · private DNS blocking · bounded JSON processing · per-API atomic quotas.</p><p class="caption">Enable Telegram two-step verification and secure the email/hosting accounts you use. These account-level settings must be enabled in those services.</p></div>`}
function showSecurityError(err){if(err.code==='STEP_UP_REQUIRED'){closeModal();go('security')}toast(err.message,true)}
function formatSelect(name,value='plain'){return `<div class="field"><label>Message format</label><select name="${name}"><option value="plain" ${value==='plain'?'selected':''}>Plain text · placeholders supported</option><option value="markdown" ${value==='markdown'?'selected':''}>Markdown · bold, italic, code and HTTPS links</option>${value==='entities'?'<option value="entities" selected>Telegram captured formatting · edit through bot</option>':''}</select><small>Markdown: *bold*, _italic_, __underline__, ~strike~, ||spoiler||, \`code\`, [label](https://example.com). Escape literal formatting markers with a backslash. No HTML.</small></div>`}
function analytics(){const d=S.statistics,series=d.series,mx=Math.max(1,...series.map(x=>x.calls)),width=560;return head('Measured activity · UTC','Daily statistics','Last seven days. Charts start with v4.7; no fabricated historical data.',button('refresh','Refresh'))+`<div class="cards">${metric('ACTIVE APIs',d.active_apis,`${d.apis} current endpoints`,'api')}${metric('CALLS TODAY',d.today.calls,'Accepted API attempts','chart')}${metric('ERRORS TODAY',d.today.errors,'Failed accepted calls','shield')}${metric(isAdmin()?'NEW USERS TODAY':'QUOTA USED',isAdmin()?d.new_users_today:d.today_used,isAdmin()?`${d.users} total accounts`:`${d.today_limit} combined active quota`,'users')}</div><div class="card"><h2>Calls per day</h2><p class="caption">Scope: ${esc(d.scope)}. User charts cover currently owned APIs; deleted API histories are not included. Workspace daily aggregates retain deleted-API traffic.</p><svg viewBox="0 0 560 170" style="width:100%;max-height:230px" role="img" aria-label="Seven-day API calls bar chart">${series.map((x,i)=>{const h=x.calls/mx*110,px=i*78+15;return `<rect x="${px}" y="${130-h}" width="40" height="${h}" rx="4" fill="#719bff"/><text x="${px+20}" y="${121-h}" fill="#b9cbed" text-anchor="middle" font-size="11">${x.calls}</text><text x="${px+20}" y="154" fill="#8c9bb1" text-anchor="middle" font-size="11">${x.day.slice(5)}</text>`}).join('')}</svg></div><div class="section" style="margin-top:20px"><div class="tablewrap"><table><thead><tr><th>UTC day</th><th>Calls</th><th>Success</th><th>Errors</th>${isAdmin()?'<th>New users</th><th>Referrals paid</th>':''}</tr></thead><tbody>${series.map(x=>`<tr><td>${x.day}</td><td>${x.calls}</td><td>${x.ok}</td><td>${x.errors}</td>${isAdmin()?`<td>${x.new_users}</td><td>${x.referrals}</td>`:''}</tr>`).join('')}</tbody></table></div></div>${isAdmin()?`<div class="card"><h2>Runtime & recovery</h2><p>Storage: ${esc(d.storage)} · Pending deliveries: ${d.queue}</p><p>Last scheduler: ${d.last_tick?date(d.last_tick)+' '+time(d.last_tick):'Not recorded'}<br>Last backup: ${d.last_backup?date(d.last_backup)+' '+time(d.last_backup):'Not recorded'}</p><p class="caption">Encrypted backups already use Firebase RTDB when configured, otherwise persistent disk. Keep the encryption key private and configure an independent S3/R2 backup if needed.</p></div>`:''}`}
function operations(){const o=S.operations;if(!o)return '<div class="notice">Owner access required.</div>';return head('Owner operations','Onboarding, logs & appearance','Configure privately. Bot tokens and Firebase backend passwords belong only in private server CONFIG/environment.')+`<div class="notice">Add your bot as administrator in every required channel/group and the private log destination. Verify joins before activation. A join-request alone is not membership. Existing API calls are not disabled by an expired five-minute onboarding check.</div><form id="operationsform"><div class="card"><h2>Join every required channel/group</h2><p class="caption">Up to five destinations. Leave a row entirely blank to omit it. Use @username or the negative numeric chat ID; private channels need a working invite link. Changes invalidate pending verification checks.</p>${Array.from({length:5},(_,i)=>{const c=o.force_join_channels[i]||{};return `<div class="grid2">${field('join_chat_'+i,`Channel/group ${i+1} ID`,c.chat_id||'')}${field('join_title_'+i,'Button label',c.title||'')}${field('join_url_'+i,'HTTPS t.me join link',c.url||'')}</div>`}).join('')}</div><div class="card" style="margin-top:20px"><h2>Private admin logs</h2>${field('log_channel','Private logs channel/group ID',o.log_channel,'text','Use a separate private -100… channel/group, not your public force-join channel.')}${field('heartbeat_minutes','Heartbeat interval · minutes (5–1440)',o.heartbeat_minutes,'number')}${field('daily_report_hour','Previous-day report hour · UTC (0–23)',o.daily_report_hour,'number')}${field('quota_warn_percent','Quota warning threshold · % (50–95)',o.quota_warn_percent,'number')}<p class="caption">A heartbeat means the authenticated scheduler ran; it cannot report its own outage. Configure external uptime monitoring for missing heartbeats. Logs omit API keys, lookup values and raw exceptions; IDs/names and operational counts may be included. Maximum 30 events/minute, with dropped-event counts.</p><p><span class="tag">${S.system.log_verified===o.log_channel&&o.log_channel&&!S.system.log_disabled?'Verified':'Not verified / disabled'}</span></p><p class="caption">${esc(S.system.log_check?.message||'Not checked yet. Verification runs on click, independently of ordinary queued messages.')} ${S.system.log_check?.test_sent?'Test message delivered.':''}</p>${button('testlogs','Verify private log destination',true)}</div><div class="card" style="margin-top:20px"><h2>Custom emoji button icons</h2><label class="checklabel"><input type="checkbox" name="supplied_emoji_enabled" ${o.supplied_emoji_enabled?'checked':''}> Use supplied premium emoji theme in messages and buttons</label><p class="caption">UTF-16-safe entities; credentials/code/links are untouched. Existing manual button IDs take priority. Telegram eligibility applies, with normal-emoji fallback. Latest message check: ${esc(S.system.supplied_emoji_delivery?.status||'Not checked')}. This is server entity retention, not a visual/client-animation test. Saving with the theme enabled clears its cooldown for another normal-message attempt. No welcome sticker is enabled.</p><p class="caption">Buttons support Telegram custom emoji icons, not sticker files. Eligibility is controlled by Telegram. Send /setbuttonemoji all (or primary/success/danger) to the bot, followed by one custom emoji, or paste numeric custom emoji IDs below. No paid emoji access is bundled. Rejected emoji payloads retry once without custom icons.</p>${['primary','success','danger'].map(style=>field('emoji_'+style,style+' icon ID',o.button_icons[style]||'')).join('')}</div><div class="actions" style="margin-top:20px"><button type="submit" class="primary">Save operations</button></div></form><div class="card" style="margin-top:20px"><h2>Referral qualification</h2><p>Inviter earns <b>${S.settings.referral_reward} coins</b>; the referred new user earns <b>${S.settings.referral_new_user_reward} coins</b>. Both are credited once after all configured joins and activation${S.settings.referral_approval?', then admin approval':''}.</p><p class="caption">New installations default to automatic rewards. Existing approval settings are preserved; change them in Settings. Rewards and source prices are configurable in Wallet & Buy. A previously registered Telegram ID cannot become a new referral.</p></div>`}

function notifications(){const seen=new Set(S.notification_seen_ids||[]);return head('Private admin activity','Notifications','Purchases, trials, API edits, redeem and credit events. Keys and query values are not included.',button('marknotifications','Mark all read',true))+`<div class="notice">Telegram admin alerts: ${S.settings.admin_event_notifications?'enabled':'disabled'}. Delivery needs a running worker or authenticated scheduler. Overview and this list refresh every 30 seconds while visible; this is not browser push.</div><div class="card">${(S.notifications||[]).map(n=>`<div class="statusrow"><div><strong>${esc(n.label)}</strong> ${seen.has(n.id)?'':'<span class="tag blue">New</span>'}<p class="caption">${date(n.t)} ${time(n.t)} · Account ${esc(n.actor)}${n.api_id?' · '+esc(n.api_id):''}${n.currency?' · charged '+n.coins_charged+' '+esc(n.currency):''}</p></div>${n.api_id&&S.apis.some(a=>a.id===n.api_id)?button('apiedit','Edit endpoint',false,n.api_id):''}</div>`).join('')||'<div class="empty">No recorded events yet. This list is populated by real actions, not sample activity.</div>'}</div>`}
function render(){$('#content').innerHTML=({overview,notifications,analytics,operations,apis,catalog,referrals,engagement,wallet,developer,users,storage,activity,backups,settings,security,docs}[view]||overview)()}
function go(v){view=v;nav();render();$('#sidebar').classList.remove('open');window.scrollTo(0,0)}
function modal(title,html,submit=null){lastFocus=document.activeElement;$('#modaltitle').textContent=title;$('#modalbody').innerHTML=html;$('#modalback').classList.remove('hidden');modalSubmit=submit;$('#modalbody input, #modalbody textarea, #modalbody button, #modalbody select')?.focus()}
function closeModal(){$('#modalback').classList.add('hidden');$('#modalbody').innerHTML='';modalSubmit=null;lastFocus?.focus()}
const formEnd=(text='Save changes')=>`<div class="modalerror" id="modalerror"></div><div class="buttonrow"><button type="button" class="ghost" data-action="closemodal">Cancel</button><button class="primary" type="submit">${text}</button></div></form>`;
function sourceFields(a={}){return `${field('name','API name',a.name||'')}${a.mode==='catalog'?'':`<div class="grid2"><div class="field"><label for="f_mode">Response mode</label><select name="mode" id="f_mode"><option value="static" ${a.mode==='static'?'selected':''}>Static JSON</option><option value="proxy" ${a.mode==='proxy'?'selected':''}>HTTPS proxy</option><option value="validation" ${a.mode==='validation'?'selected':''}>Offline validation only</option></select></div>${field('param','Input parameter',a.param||'value','text','Independent per source. Use authorized, non-sensitive inputs.')}</div><div id="staticfields">${area('data','JSON response',a.data??{message:'Hello, world'})}</div><div id="proxyfields">${field('url','Approved source URL',a.url||'','url','Exact host must be on the allowlist. Keep provider keys private. No redirects.')}<div id="sourcehosthint" class="notice"></div></div><div id="validationfields"><div class="field"><label for="f_validator">Validator</label><select id="f_validator" name="validator"><option value="phone_format" ${a.validator!=='aadhaar_checksum'?'selected':''}>Indian mobile format — no subscriber lookup</option><option value="aadhaar_checksum" ${a.validator==='aadhaar_checksum'?'selected':''}>Aadhaar format/checksum — no identity lookup</option></select></div><p class="caption">No external provider call, no private records, no identity verification. Empty example defaults to an all-zero synthetic invalid input.</p></div><div id="inputfields">${field('example_value','Public synthetic example',a.example_value||'','text','Required for proxies. Never put secrets or a real private record here.')}</div><div id="demofields"><div class="field"><label for="f_demo_response">Demo response JSON — optional synthetic sample</label><textarea id="f_demo_response" name="demo_response" rows="4" maxlength="1200">${esc(Object.prototype.hasOwnProperty.call(a,'demo_response')?JSON.stringify(a.demo_response,null,2):'')}</textarea><small>Up to 1200 bytes after JSON encoding. A preview never calls the provider or spends customer coins.</small></div></div>`}`}
function syncMode(){const mode=$('#f_mode')?.value;for(const [id,show] of [['staticfields',mode==='static'],['proxyfields',mode==='proxy'],['validationfields',mode==='validation'],['inputfields',mode!=='static'],['demofields',mode!=='validation']])if($('#'+id))$('#'+id).classList.toggle('hidden',!show);sourceHostHint()}
function sourceData(f){const d=Object.fromEntries(new FormData(f));if(d.mode==='proxy'&&d.url)d.url=d.url.replace(/&(?:amp;)+/g,'&');if(d.mode==='static')d.data=JSON.parse(d.data);else delete d.data;if(d.mode!=='validation'&&d.demo_response?.trim())d.demo_response=JSON.parse(d.demo_response);else delete d.demo_response;return d}
function showKey(r){modal('Save your private API credentials',`${r.is_trial?`<div class="notice">TRIAL · expires ${date(r.expires)} · ${r.trial_limit} total requests; no reset.</div>`:''}<div class="notice warn">Save the TXT now. Only the key hash is stored in the endpoint; the original key cannot be retrieved later. Do not paste keyed URLs into chats. Header-only protection is ${r.header_only?'ON':'OFF (available in endpoint settings)'}.</div>${field('newkey','API key',r.key)}${field('endpoint','Endpoint without credentials',r.endpoint||location.origin+'/api/'+r.id)}<div class="field"><label>Private TXT content</label><textarea id="receipt_text" data-filename="${esc(r.id)}.txt" rows="9" readonly>${esc(r.credential_text||'API key: '+r.key)}</textarea></div><details><summary>${r.header_only?'Request URL (requires header authentication)':'Legacy keyed URL — optional, keep private'}</summary>${field('readyurl','URL',r.ready_url||'')}</details><div class="buttonrow">${button('downloadcredentials','Download private TXT',true)}${button('copynewkey','Copy key')}${button('closemodal','Done')}</div>`);$('#f_newkey').readOnly=true;$('#f_endpoint').readOnly=true;$('#f_readyurl').readOnly=true}

function createModal(cid){if(cid){const c=S.catalog.find(x=>x.id===cid),plans=(c.plans||[]).filter(p=>p.enabled!==false);modal('Create from catalogue',`<form id="modalform"><div class="notice">${esc(c.name)} · ${isAdmin()?'Admin test: no coins charged.':'Confirm your selected plan.'}${!c.plans?.length?`<br>${S.settings.daily_limit}/day · ${S.settings.valid_days} days · ${esc(priceText(c))}`:''}</div>${c.plans?.length?`<label class="field">Plan<select name="chosen_plan" required>${plans.map(p=>`<option value="${esc(p.id)}">${esc(p.name)} · ${p.price} coins · ${p.days} days · ${p.daily}/day · ${p.rpm}/min${p.total?' · '+p.total+' total':''}</option>`).join('')}</select></label>`:''}${field('name','Your API name',c.name)}${formEnd('Create API')}`,async f=>{const plan=plans.find(p=>p.id===f.elements.chosen_plan?.value);if(c.plans?.length&&!plan)throw new Error('No enabled plan. Edit the source first.');const r=await req('/manage/apis',{catalog_id:cid,name:f.elements.name.value,quote_price:plan?plan.price:c.price??S.settings.default_api_price,quote_currency:plan?'coins':c.billing_currency||'coins',...(plan?{plan_id:plan.id,quote_plan:plan}:{})});closeModal();await refresh();showKey(r)});return}modal('Create admin test endpoint',`<form id="modalform"><div class="notice">This creates your own test endpoint, not a category for customers. To sell a source, use API catalogue → Add source.<br>${S.settings.daily_limit} daily requests · ${S.settings.valid_days} days · ${isAdmin()?0:S.settings.default_api_price} coins</div>${sourceFields()}${formEnd('Create API')}`,async f=>{const r=await req('/manage/apis',{...sourceData(f),quote_price:S.settings.default_api_price,quote_currency:'coins'});closeModal();await refresh();showKey(r)});syncMode()}
function editApi(id){const a=S.apis.find(a=>a.id===id),src=a.mode==='catalog'?S.catalog.find(c=>c.id===a.catalog_id):null,locked=isAdmin()&&!ISDEMO&&!S.settings.owner_approval_required&&S.security.elevated_until<=Date.now()/1000;modal('Edit endpoint settings',`<div class="actions" style="margin-bottom:18px">${status(a)}<span class="chip">${esc(a.id)}</span></div>${locked?`<div class="notice warn">Editing another user's endpoint or enabling public access requires fresh security confirmation. ${button('opensecurity','Unlock sensitive edits')}</div>`:''}${src?`<div class="notice"><b>Shared source: ${esc(src.name)}</b><br>Customer parameter: <code>${esc(src.param||'(none)')}</code>. Provider URL/input/example live in the source, not this endpoint.<br>Save endpoint changes before opening the source editor. Shared source edits affect ${S.apis.filter(x=>x.catalog_id===src.id).length} bound endpoints.<div class="actions">${button('editcatalog','Edit shared source',false,src.id)}</div></div>`:''}${a.plan_snapshot?`<div class="notice">Purchased plan: ${esc(a.plan_snapshot.name)}. Catalogue plan edits affect new purchases only. Explicit overrides below change this endpoint; renewal reapplies its saved daily/RPM policy.</div>`:''}${a.is_trial?`<div class="notice">TRIAL: ${a.calls}/${a.trial_limit} total requests · fixed deadline ${date(a.trial_deadline)}. Only the name is editable.</div>`:''}<form id="modalform">${sourceFields(a)}${isAdmin()&&!a.is_trial?`<div class="grid2">${field('daily','Daily limit',a.daily,'number')}${field('rpm','Per-minute limit',a.rpm,'number')}${field('total_limit','Lifetime total cap · 0 = none',a.total_limit||0,'number')}${field('extend_days','Extend validity · days',0,'number')}</div><label class="checklabel"><input name="set_exact_expiry" type="checkbox"> Override exact expiry instead of adding days</label>${field('expires_at','Exact expiry · UTC',new Date(a.expires*1000).toISOString().slice(0,16),'datetime-local')}<label class="checklabel"><input name="header_only" type="checkbox" ${a.header_only?'checked':''}> Require X-API-Key / Bearer headers; reject keyed URLs and link previews</label><label class="checklabel"><input name="public" type="checkbox" ${a.public?'checked':''}> Public endpoint · no key required (cannot combine with header-only)</label><p class="caption">Enabling header-only breaks existing query-key integrations until they send a header. This does not rotate the key. Usage is never reset by saving.</p>`:''}${formEnd('Save endpoint settings')}<div class="divider"></div><div class="actions">${button('apitoggle',a.active?'Pause API':'Enable API',false,id)}${a.is_trial?'':button('apirenew','Renew',false,id)}${button('apirotate','Rotate key / new TXT',false,id)}<button class="danger" data-action="apidelete" data-id="${esc(id)}">Delete</button></div><div class="divider"></div><h3>Usage & history</h3><p class="caption">${a.used}/${a.daily} today · ${a.calls} total${a.total_limit?' / '+a.total_limit+' cap':''} · ${a.errors} upstream failures<br>Expires ${date(a.expires)} ${time(a.expires)} · Owner ${esc(a.owner)}</p><div class="actions">${button('testapi','Test endpoint',false,id)}${button('copyendpoint','Copy endpoint without key',false,id)}</div><div class="tablewrap" style="margin-top:14px"><table><thead><tr><th>Time</th><th>Result</th><th>Latency</th></tr></thead><tbody>${(a.history||[]).slice(-8).reverse().map(h=>`<tr><td>${time(h.t)}</td><td>${h.ok?'OK':'Error'}</td><td>${h.ms}ms</td></tr>`).join('')||'<tr><td colspan="3">No recent calls</td></tr>'}</tbody></table></div>`,async f=>{const d=a.mode==='catalog'?{name:f.elements.name.value}:sourceData(f);if(isAdmin()&&!a.is_trial){d.daily=+f.elements.daily.value;d.rpm=+f.elements.rpm.value;d.total_limit=+f.elements.total_limit.value;d.extend_days=+f.elements.extend_days.value;d.public=f.elements.public.checked;d.header_only=f.elements.header_only.checked;if(f.elements.set_exact_expiry.checked){if(d.extend_days)throw new Error('Use exact expiry OR extra days, not both.');d.expires_at=Math.floor(Date.parse(f.elements.expires_at.value+'Z')/1000);if(!Number.isFinite(d.expires_at))throw new Error('Choose a valid expiry.');}}await req('/manage/apis/'+id+'/edit',d);closeModal();await refresh();toast('Endpoint settings saved. Usage preserved.')});syncMode()}

function planRow(p={}){const pid=p.id||('p_'+Math.random().toString(36).slice(2,10));return `<div data-plan-row class="card" style="margin:12px 0;padding:14px"><div class="grid2">${[['id','Stable plan ID',pid,'text'],['name','Plan name',p.name||'Starter','text'],['price','Coins',p.price??250,'number'],['days','Days',p.days??10,'number'],['daily','Requests / day',p.daily??100,'number'],['rpm','Requests / minute',p.rpm??30,'number'],['total','Total cap · 0 = none',p.total??0,'number']].map(([k,label,v,t])=>`<label class="field">${label}<input name="plan_${k}" type="${t}" value="${esc(v)}" ${k==='id'?'readonly':''} required></label>`).join('')}</div><label class="checklabel"><input name="plan_enabled" type="checkbox" ${p.enabled!==false?'checked':''}> Available for new purchases</label><button type="button" class="ghost small" data-action="removeplanrow" data-id="${esc(pid)}">Remove plan</button></div>`}
function readPlans(f){return [...f.querySelectorAll('[data-plan-row]')].map(row=>{const val=k=>row.querySelector('[name="plan_'+k+'"]').value;return {id:val('id'),name:val('name'),price:+val('price'),days:+val('days'),daily:+val('daily'),rpm:+val('rpm'),total:+val('total'),enabled:row.querySelector('[name=plan_enabled]').checked,billing_currency:'coins'}})}
function rewardTools(){modal('Owner rewards & credits',`<div class="notice">Owner-only financial actions. Existing credits are not reversed by revoking a code. Code text is shown only when created.</div><div class="actions">${button('newredeem','Create redeem code',true)}${button('credituser','Add user coins')}</div><h3>Redeem records</h3>${(S.redeem_codes||[]).map(r=>`<div class="card"><code>${esc(r.id)}</code><p>${r.coins} coins · ${r.claimed}/${r.uses} users · expires ${date(r.expires)} · ${r.enabled?'Enabled':'Revoked'}</p>${r.enabled?button('revokecode','Revoke',false,r.id):''}</div>`).join('')||'<p>No codes created yet.</p>'}`)}
function catalogModal(id){const c=S.catalog.find(c=>c.id===id)||{};modal(id?'Edit customer source':'Add source for customers',`<form id="modalform"><div class="notice">This is a SHARED SOURCE. Provider URL, input name and example changes affect bound endpoints. Plan/price changes affect new purchases, not existing plan contracts. To edit one customer’s quota/auth/expiry use Endpoints → Manage. Sensitive changes require owner approval or security confirmation according to policy. No external lookup is made by this form.</div>${sourceFields(c)}<div class="grid2">${currencyField(c.billing_currency)}${field('price','Legacy/default price · no plans',c.price??S.settings.default_api_price,'number')}</div><h3>Customer plans</h3><p class="caption">Add up to 8 coin plans. When plans exist, customers must choose one. Purchased limits/price are saved; later edits apply only to new purchases. Daily cap and optional total cap both apply. Renewal adds the saved days and total budget without resetting usage.</p><div id="planrows">${(c.plans||[]).map(p=>planRow(p)).join('')}</div>${button('addplanrow','+ Add plan')}<div class="divider"></div><p class="caption">Query name and example are independent for each source. Price changes apply to newly created APIs; existing APIs retain their renewal price.</p><label class="checklabel"><input type="checkbox" name="enabled" ${c.enabled!==false?'checked':''}> Enabled for user subscriptions</label><label class="checklabel"><input type="checkbox" name="trial_enabled" ${c.trial_enabled?'checked':''}> Explicitly allow short demo access to THIS source</label><label class="checklabel"><input type="checkbox" name="starter_enabled" ${c.starter_enabled?'checked':''}> Allow the separate free starter API on this source</label><p class="caption">Off by default. Turning this off also stops active trial keys; paid subscriptions are unaffected.</p>${formEnd()}${id?`<div class="divider"></div><button class="danger" data-action="deletecatalog" data-id="${esc(id)}">Delete source</button>`:''}`,async f=>{await req('/manage/admin/catalog',{...sourceData(f),plans:readPlans(f),id,price:+f.elements.price.value,enabled:f.elements.enabled.checked,trial_enabled:f.elements.trial_enabled.checked,starter_enabled:f.elements.starter_enabled.checked});closeModal();await refresh();toast('Catalogue saved.')});syncMode()}
function userModal(id){const u=S.users.find(x=>x.id===id);modal('Manage member',`<form id="modalform"><div class="notice">${esc(u.name)} · ${esc(u.id)}</div>${isSuper()?`<div class="field"><label>Role</label><select name="role"><option value="user" ${u.role==='user'?'selected':''}>User</option><option value="admin" ${u.role==='admin'?'selected':''}>Admin</option></select></div>${field('coins','Coin balance',u.coins,'number')}${field('diamonds','Diamond balance',u.diamonds,'number')}<p class="caption">Balance adjustments are owner-only, audited and require fresh confirmation. Negative refund debts should be reconciled, not silently erased.</p>`:''}<label class="checklabel"><input name="blocked" type="checkbox" ${u.blocked?'checked':''}> Suspend account and its API access</label>${formEnd()}${isSuper()?`<div class="divider"></div><p class="caption">Deletion requires removing owned APIs first. A blocked tombstone is retained to prevent repeat referral rewards.</p><button class="danger" data-action="deleteuser" data-id="${esc(id)}">Delete account</button>`:''}`,async f=>{let d={id,blocked:f.elements.blocked.checked};if(isSuper()){d.role=f.elements.role.value;d.coins=+f.elements.coins.value;d.diamonds=+f.elements.diamonds.value}await req('/manage/admin/user',d);closeModal();await refresh();toast('Member updated.')})}
function kvModal(key){modal(key?'Edit record':'Add JSON record',`<form id="modalform">${field('key','Record key',key||'')}${area('value','JSON value',key?S.kv[key]:{})}${formEnd()}${key?`<div class="divider"></div><button class="danger" data-action="deletekv" data-id="${esc(key)}">Delete record</button>`:''}`,async f=>{await req('/manage/admin/kv',{key:f.elements.key.value,value:JSON.parse(f.elements.value.value)});closeModal();await refresh();toast('Record saved.')});if(key)$('#f_key').readOnly=true}
async function handleAction(action,id){
 if(action==='downloadcredentials'){const el=$('#receipt_text'),url=URL.createObjectURL(new Blob([el.value],{type:'text/plain;charset=utf-8'})),a=document.createElement('a');a.href=url;a.download=el.dataset.filename;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}
 else if(action==='opensecurity'){closeModal();go('security');}
 else if(action==='opennotifications'||action==='marknotifications'){await req('/manage/notifications/read',{});await refresh();go('notifications');}
 else if(action==='removeplanrow'){const row=[...$('#planrows').children].find(r=>r.querySelector('[name=plan_id]').value===id);if(row)row.remove();}
 else if(action==='addplanrow'){const box=$('#planrows');if(box.children.length>=8)throw new Error('Maximum eight plans.');box.insertAdjacentHTML('beforeend',planRow());}
 else if(action==='rewardtools'){rewardTools();}
 else if(action==='revokecode'){if(!confirm('Revoke this code for future claims?'))return;await req('/manage/admin/redeem',{id,revoke:true});await refresh();rewardTools();}
 else if(action==='newredeem'){modal('Create redeem code',`<form id="modalform"><div class="notice">A gift code grants coins once per registered eligible user, up to your cap.</div>${field('coins','Coins per user',50,'number')}${field('uses','Maximum users',1,'number')}${field('days','Valid days',7,'number')}${formEnd('Create code')}`,async f=>{const r=await req('/manage/admin/redeem',{coins:+f.elements.coins.value,uses:+f.elements.uses.value,days:+f.elements.days.value});await refresh();modal('Save your redeem code',`<div class="notice warn">Shown once. Save privately before closing.</div><pre id="newgiftcode" class="callcode">${esc(r.code)}</pre>${button('copygift','Copy code',true)}<p>Record: <code>${esc(r.id)}</code></p><p>${r.coins} coins · ${r.uses} users · expires ${date(r.expires)}</p>${button('closemodal','Done')}`)});}
 else if(action==='copygift'){await copy($('#newgiftcode').textContent);}
 else if(action==='credituser'){modal('Add user coins',`<form id="modalform"><div class="notice">Owner adjustment, not automatic proof of payment. Reusing the same reference will not credit twice.</div>${field('uid','Registered Telegram user ID','','text')}${field('coins','Coins to add',50,'number')}${field('reference','Unique adjustment reference','','text','Example: bonus_oct01_user123')}${formEnd('Review and credit')}`,async f=>{if(!confirm('Credit '+f.elements.coins.value+' coins to '+f.elements.uid.value+'?'))return;const r=await req('/manage/admin/credit',{uid:f.elements.uid.value.trim(),coins:+f.elements.coins.value,reference:f.elements.reference.value.trim()});closeModal();await refresh();toast(r.message)});}
 else if(action==='previewsource'){previewSource(id);}else if(action==='opencatalog'){closeModal();view='catalog';nav();render();}else if(action==='openhostsettings'){closeModal();view='settings';nav();render();}else if(action==='openoperations'){closeModal();view='operations';nav();render();}else if(action==='opendocs'){view='docs';nav();render();}else if(action==='refresh'){await refresh();toast('Workspace refreshed.')}else if(action==='logout'){await req('/logout',{});location.reload()}else if(action==='switchdemo'){await req('/demo-login',{role:S.me.role==='user'?'admin':'user'});location.reload()}else if(action==='closemodal')closeModal();else if(action==='copyref')await copy(S.referral_url);else if(action==='create')createModal();else if(action==='fromcatalog')createModal(id);else if(action==='apiedit')editApi(id);else if(action==='copyreadyurl')await copy($('#f_readyurl').value);else if(action==='copynewkey')await copy($('#f_newkey').value);else if(action==='copyendpoint')await copy(location.origin+'/api/'+id);else if(action==='newdemosource'){catalogModal();$('#modaltitle').textContent='Add safe demo JSON source';$('#f_name').value='Demo JSON';$('#f_data').value=JSON.stringify({status:'success',service:'SR DARK',message:'Your API is working. This is sample data.'},null,2);$('#modalbody input[name="trial_enabled"]').checked=true;}else if(action==='newcatalog')catalogModal();else if(action==='editcatalog')catalogModal(id);else if(action==='edituser')userModal(id);else if(action==='newkv')kvModal();else if(action==='editkv')kvModal(id);

 else if(action==='revokeothers'||action==='revokesession'){if(!confirm('Sign out the selected other browser session(s)?'))return;const r=await req('/manage/security/revoke',{id:action==='revokeothers'?'others':id});await refresh();toast(r.message)}
 else if(action==='dailybroadcast'){campaignModal();$('#modaltitle').textContent='Daily broadcast · review before enabling';$('#f_name').value='Daily API news';$('#f_min_hours').value=24;$('#f_max_hours').value=24;$('#campaign_text').value='Hi {name} 💙\nAPI tip: keep your personal key private and check usage before making requests. Open My APIs below to manage your endpoints. New here? Try your one-time API trial.\nHave a question? Use /help or /paysupport in this bot.';}
 else if(action==='newcampaign'||action==='editcampaign'){campaignModal(id)}
 else if(action==='testlogs'){const r=await req('/manage/operations/testlogs',{});await refresh();toast(r.message,r.status!=='verified')}
 else if(action==='copycampaigncmd'){await copy('/setcampaign '+id)}
 else if(action==='copywelcomecmd'){await copy('/setwelcome')}
 else if(action==='updateson'||action==='updatesoff'){const r=await req('/manage/engagement/preferences',{enabled:action==='updateson'});await refresh();toast(r.message)}
 else if(action==='welcomepreview'||action==='previewcampaign'){const target=$('#promo_preview_target')?.value;if(!target)throw new Error('Register a Telegram admin with /start first.');const r=await req('/manage/engagement/preview',{target,campaign_id:action==='previewcampaign'?id:''});toast(r.message)}
 else if(['togglecampaign','runcampaign','deletecampaign'].includes(action)){if(action==='deletecampaign'&&!confirm('Delete this campaign and cancel queued deliveries? Already in-flight messages cannot be recalled.'))return;if(action==='runcampaign'&&!confirm('Queue an eligible-recipient scan for the next scheduler tick? Audience eligibility, quiet hours and daily caps still apply.'))return;const op={togglecampaign:'toggle',runcampaign:'run',deletecampaign:'delete'}[action];const r=await req('/manage/campaigns/'+id+'/'+op,{});await refresh();toast(r.message)}
 else if(action==='newpack'||action==='editpack'){packModal(id)}
 else if(action==='buystars'){const p=S.settings.purchase_packs.find(p=>p.id===id);if(!confirm(`Buy ${p.amount} ${p.currency} for ${p.stars} Telegram Stars? Read the purchase terms before paying. An invoice will be sent to your bot chat.`))return;const r=await req('/manage/wallet/buy',{pack_id:id});await refresh();toast(r.message)}
 else if(action==='buyupi'){manualPurchase(id)}
 else if(action==='approvepayment'||action==='rejectpayment'){let verification='';if(action==='approvepayment'){verification=prompt('Check the exact amount, reference and sender in your OWN bank account. Screenshots are not verification. Type VERIFIED to credit this purchase.');if(verification!=='VERIFIED')return}else if(!confirm('Reject this manual payment request?'))return;const r=await req('/manage/payments/'+id+'/'+(action==='approvepayment'?'approve':'reject'),{verification});await refresh();toast(r.message)}
 else if(action==='refundpayment'){if(!confirm('Refund this Stars payment? Purchased units are removed once. Spent funds can leave a negative wallet and pause API access. Uncertain network results remain refund_pending until reconciled.'))return;const r=await req('/manage/payments/'+id+'/refund',{});await refresh();toast(r.message)}
 else if(action==='activate'){await req('/manage/activate',{});await refresh();toast('Account activated.')}
 else if(['apitoggle','apirenew','apirotate','apidelete'].includes(action)){const op={apitoggle:'toggle',apirenew:'renew',apirotate:'rotate',apidelete:'delete'}[action];if(op!=='toggle'&&!confirm({renew:`Spend ${isAdmin()?'0 (admin)':priceText(S.apis.find(a=>a.id===id))} to extend validity ${S.settings.valid_days} days?`,rotate:'Rotate key? The old key will stop immediately.',delete:'Permanently delete this API? No balance refund.'}[op]))return;const r=await req('/manage/apis/'+id+'/'+op,{});closeModal();await refresh();if(r.key)showKey(r);else toast(r.message||'API updated.')}
 else if(action==='testapi'){const a=S.apis.find(x=>x.id===id),src=a.mode==='catalog'?S.catalog.find(c=>c.id===a.catalog_id)||{}:a;modal('Test JSON endpoint',`<form id="modalform"><div class="notice">An authenticated test consumes quota, even if the upstream fails.</div>${a.public?'':field('key','API key (not stored in this panel)','','password')}${field('param','Parameter name',src.param||'value')}${field('value','Test value',src.example_value||'')}<div class="modalerror" id="modalerror"></div><button class="primary" type="submit">Send request</button></form><pre id="testout" class="callcode">Ready.</pre>`,async f=>{const q=new URLSearchParams();if(f.elements.value.value)q.set(f.elements.param.value,f.elements.value.value);const r=await fetch('/api/'+id+'?'+q.toString(),{headers:{'X-API-Key':f.elements.key?.value||''}});$('#testout').textContent='HTTP '+r.status+'\n'+JSON.stringify(await r.json(),null,2)})}
 else if(action==='deletecatalog'){if(!confirm('Delete this catalogue source? Active subscriptions prevent deletion.'))return;await req('/manage/admin/catalog',{id,delete:true});closeModal();await refresh()}
 else if(action==='deleteuser'){if(!confirm('Delete this account? A blocked anti-abuse tombstone will remain.'))return;await req('/manage/admin/user',{id,delete:true});closeModal();await refresh()}
 else if(action==='deletekv'){if(!confirm('Delete this JSON record?'))return;await req('/manage/admin/kv',{key:id,delete:true});closeModal();await refresh()}
 else if(action==='approveref'||action==='rejectref'){await req('/manage/admin/referral',{id,approve:action==='approveref'});await refresh();toast('Referral reviewed.')}
 else if(action==='backup'){toast('Creating encrypted snapshot…');const r=await req('/manage/backup',{});await refresh();toast(r.message)}
 else if(action==='export'){const r=await req('/manage/export',null,'GET','',true);const url=URL.createObjectURL(await r.blob());const link=document.createElement('a');link.href=url;link.download='srdark-backup.enc';link.click();setTimeout(()=>URL.revokeObjectURL(url),1000)};
}
document.addEventListener('click',async e=>{const el=e.target.closest('button');if(!el)return;if(el.dataset.view){go(el.dataset.view);return}if(!el.dataset.action)return;e.preventDefault();el.disabled=true;try{await handleAction(el.dataset.action,el.dataset.id)}catch(err){showSecurityError(err)}finally{el.disabled=false}});
document.addEventListener('change',e=>{if(e.target.id==='f_mode')syncMode();if(e.target.id==='campaign_trigger')syncCampaignFields()});
document.addEventListener('input',e=>{if(e.target.id==='apisearch'){const q=e.target.value.toLowerCase();$('#apitable').innerHTML=apiTable(S.apis.filter(a=>(a.name+' '+a.id).toLowerCase().includes(q)))}if(e.target.id==='usersearch'){const q=e.target.value.toLowerCase();$('#usertable').innerHTML=userRows(S.users.filter(u=>(u.name+' '+u.id).toLowerCase().includes(q)))}});
document.addEventListener('submit',async e=>{e.preventDefault();const f=e.target, b=f.querySelector('button[type=submit]');if(b)b.disabled=true;try{
 if(f.id==='modalform'&&modalSubmit){if($('#modalerror'))$('#modalerror').textContent='';await modalSubmit(f)}
 else if(f.id==='confirmform'){await req('/manage/security/verify',{code:f.elements.code.value.trim()});location.reload()}
 else if(f.id==='firebaseloginform'){try{$('#firebaseerror').textContent='';const token=await firebasePasswordToken($('#fbemail').value.trim(),$('#fbpassword').value);await req('/login/firebase',{id_token:token});location.reload()}finally{$('#fbpassword').value=''}}
 else if(f.id==='firebaseconfirmform'){try{const token=await firebasePasswordToken(f.elements.email.value,f.elements.password.value);await req('/manage/security/firebase',{id_token:token});location.reload()}finally{f.elements.password.value=''}}
 else if(f.id==='loginform'){await req('/login',{code:$('#logincode').value.trim()});location.reload()}
 else if(f.id==='conversionform'){const amount=+f.elements.convert_amount.value,rate=S.settings.diamond_coin_rate;if(!confirm(`Convert ${amount} diamonds into ${amount*rate} coins? This cannot be reversed.`))return;const r=await req('/manage/wallet/convert',{amount,rate});await refresh();toast(r.message)}
 else if(f.id==='operationsform'){const d={supplied_emoji_enabled:f.elements.supplied_emoji_enabled.checked,force_join_channels:[],log_channel:f.elements.log_channel.value.trim(),heartbeat_minutes:+f.elements.heartbeat_minutes.value,daily_report_hour:+f.elements.daily_report_hour.value,quota_warn_percent:+f.elements.quota_warn_percent.value,button_icons:{}};for(let i=0;i<5;i++){const chat_id=f.elements['join_chat_'+i].value.trim(),title=f.elements['join_title_'+i].value.trim(),url=f.elements['join_url_'+i].value.trim();if(chat_id||title||url){if(!chat_id||!title||!url)throw new Error('Complete all three fields for every required channel/group.');d.force_join_channels.push({chat_id,title,url})}}for(const style of ['primary','success','danger'])d.button_icons[style]=f.elements['emoji_'+style].value.trim();const r=await req('/manage/operations',d);await refresh();toast(r.message)}
 else if(f.id==='engagementform'){const d={welcome_dashboard:f.elements.welcome_dashboard.checked,remove_video:f.elements.remove_video?.checked||false,welcome_mode:f.elements.welcome_mode.value,welcome_caption:f.elements.welcome_caption.value,welcome_links:readPromoLinks(f,'welcome'),campaigns_enabled:f.elements.campaigns_enabled.checked,campaign_timezone:f.elements.campaign_timezone.value,remove_photo:f.elements.remove_photo?.checked||false};for(const n of ['delivery_start_hour','delivery_end_hour','campaign_daily_cap','campaign_gap_hours'])d[n]=+f.elements[n].value;await req('/manage/engagement/settings',d);await refresh();toast('Welcome and delivery policy saved.')}
 else if(f.id==='economyform'){const d=Object.fromEntries(new FormData(f));for(const n of ['default_api_price','referral_reward','referral_new_user_reward','diamond_coin_rate'])d[n]=+d[n];await req('/manage/admin/settings',d);await refresh();toast('Wallet policy saved.')}
 else if(f.id==='developerform'){await req('/manage/admin/settings',Object.fromEntries(new FormData(f)));await refresh();toast('Developer profile saved.')}
 else if(f.id==='settingsform'){const d=Object.fromEntries(new FormData(f));for(const n of ['bot_user_rpm','bot_admin_rpm','starter_days','starter_daily','starter_rpm','starter_extend_price','starter_extend_days','starter_quota_price','starter_quota_add','custom_key_price','web_unlock_minutes','trial_minutes','trial_requests','trial_rpm','default_api_price','daily_limit','valid_days','rpm','max_apis','max_payload_kb','backup_hours','backup_keep'])d[n]=+d[n];for(const n of ['allowed_hosts','replace','inject'])d[n]=JSON.parse(d[n]);for(const n of ['modern_controls','starter_enabled','safe_chat_receipts','owner_approval_required','trial_enabled','referral_approval','allow_custom','apply_existing','api_receipts_txt','admin_event_notifications','default_header_only'])d[n]=f.elements[n].checked;await req('/manage/admin/settings',d);await refresh();toast('Platform settings saved.')}
 else if(f.id==='restoreform'){if(!confirm('Replace ALL v4 data with this encrypted backup?'))return;const d=new FormData(f);d.append('csrf',CSRF);await req('/manage/restore',d);location.reload()}
 }catch(err){if(err.code==='STEP_UP_REQUIRED'){showSecurityError(err);return}if(f.id==='firebaseloginform')$('#firebaseerror').textContent=err.message;else if(f.id==='loginform')$('#loginerror').textContent=err.message;else if(f.id==='modalform'&&$('#modalerror'))$('#modalerror').textContent=err.message;else toast(err.message,true)}finally{if(b)b.disabled=false}});
$('#modalback').addEventListener('click',e=>{if(e.target===$('#modalback'))closeModal()});document.addEventListener('keydown',e=>{if(e.key==='Escape')closeModal();if(e.key==='Tab'&&!$('#modalback').classList.contains('hidden')){let els=[...$('#modalback').querySelectorAll('button,input,select,textarea,a')].filter(el=>!el.disabled&&el.offsetParent!==null);if(!els.length)return;if(e.shiftKey&&document.activeElement===els[0]){e.preventDefault();els.at(-1).focus()}else if(!e.shiftKey&&document.activeElement===els.at(-1)){e.preventDefault();els[0].focus()}}});
if($('#menubtn'))$('#menubtn').onclick=()=>$('#sidebar').classList.toggle('open');
if($('#demoadmin'))$('#demoadmin').onclick=async()=>{await req('/demo-login',{role:'admin'});location.reload()};if($('#demouser'))$('#demouser').onclick=async()=>{await req('/demo-login',{role:'user'});location.reload()};
if(LOGGED){refresh().catch(err=>{$('#content').innerHTML=`<div class="notice warn">${esc(err.message)}</div><button data-action="logout">Return to login</button>`});setInterval(()=>{if(['overview','notifications'].includes(view)&&$('#modalback').classList.contains('hidden')&&!document.hidden)refresh().catch(()=>{})},30000)}
</script></body></html>
'''

def seed_demo():
    def seed(s):
        if s["users"]: return
        for uid,name,coins in [("10001","Droid",50),("10002","Aarav Sharma",5),("10003","Maya Singh",3),("10004","Rohan Mehta",2)]:
            register(s,uid,name); s["users"][uid].update(active=True,coins=coins*50,diamonds=5,refs=coins)
        s["outbox"]={}
        s["catalog"]["cat_weather"]={"id":"cat_weather","name":"Weather sample","mode":"static","data":{"city":"Patna","temperature":29,"condition":"Clear","sample":True},"url":"","param":"city","enabled":True}
        for uid,name,data in [("10001","Product catalogue",{"products":[{"id":1,"name":"Starter","price":199}]}),("10001","Service health",{"status":"healthy","region":"ap-south"}),("10002","My first endpoint",{"message":"Hello, world"})]:
            if simple_ui(s) and not is_admin(uid,s):
                cid='cat_demo_'+uid;s['catalog'][cid]={'id':cid,'name':name,'mode':'static','data':data,'enabled':True}
                create_api(s,uid,{'catalog_id':cid,'name':name})
            else:create_api(s,uid,{"name":name,"data":data})
        # Clearly labelled demo-only activity for the interactive preview.
        for idx,a in enumerate(s["apis"].values()):
            a["calls"]=[236,84,31][idx]; a["used"]=[36,18,7][idx]
            a["history"]=[{"t":now()-((j*137+idx*211)%3500),"ok":True,"ms":12+j%17} for j in range(30)]
        s["users"]["10002"]["coins"]=250
        s["kv"]["welcome"]={"message":"Welcome to SR DARK"}
        audit(s,"system","demo.seed","Sample data. Telegram/cloud are not connected.")
    store.tx(seed)

if DEMO and store: seed_demo()

def run_worker():
    require(store is not None and not DEMO,'Configure production storage before starting the worker.',503)
    next_tick=0
    flag=cfg('BOOTSTRAP_V4171_CHAT_URLS');fast=flag is True or str(flag).lower() in ('1','true','yes')
    while True:
        try:
            requested=_WORKER_WAKE.is_set();_WORKER_WAKE.clear();sent=0
            if fast:sent=drain(6,3) if requested or store.read().get('outbox') else 0
            if time.monotonic()>=next_tick:
                def maintenance(s):
                    operational_tick(s);engagement_tick(s);prune_security_state(s);prune_approvals(s)
                store.tx(maintenance);schedule_backup_async();next_tick=time.monotonic()+60
            if not fast:sent=drain(6,3) if requested or store.read().get('outbox') else 0
            if sent>=6:wake_worker()
        except Exception:
            LOG.warning('Worker operation failed; durable jobs retained for retry')
            next_tick=max(next_tick,time.monotonic()+30)
        if cfg('BOOTSTRAP_V416_FOCUSED_UI') is True or str(cfg('BOOTSTRAP_V416_FOCUSED_UI')).lower() in ('true','1','yes'):_WORKER_WAKE.wait(2)
        else:time.sleep(2)

def cli():
    p=argparse.ArgumentParser(description="SR DARK 4 single-file API console and Telegram webhook bot. Deployment guide: module header / DEPLOY-GUIDE.md.")
    p.add_argument("--demo",action="store_true"); p.add_argument("--new-secret",action="store_true")
    p.add_argument("--set-webhook",action="store_true"); p.add_argument("--tick",action="store_true");p.add_argument("--worker",action="store_true")
    p.add_argument("--restore",metavar="BACKUP.enc"); p.add_argument("--yes",action="store_true")
    p.add_argument("--port",type=int,default=int(os.environ.get("PORT","8080")))
    args=p.parse_args()
    if args.new_secret: print(secrets.token_urlsafe(48)); return
    if args.set_webhook:
        print(configure_webhook()); return
    if args.worker:run_worker();return
    if args.tick:
        require(store is not None,"Configure storage first."); store.tx(operational_tick); print("Engagement",store.tx(engagement_tick)); print(run_backup()); print("Delivered",drain(10)); store.tx(lambda s:s["system"].update(last_tick=now())); return
    if args.restore:
        require(args.yes,"Restore replaces all current v4 data. Pass --yes after saving a backup.")
        require(store is not None,"Configure storage first."); restore_blob(Path(args.restore).read_bytes()); print("Restored."); return
    if DEMO:app.run(host="0.0.0.0",port=args.port,debug=False)
    else:
        from gunicorn.app.base import BaseApplication
        class Server(BaseApplication):
            def load_config(self):
                for k,v in {'bind':'0.0.0.0:'+str(args.port),'workers':1,'worker_class':'gthread','threads':4,'timeout':120,'post_worker_init':lambda worker:start_embedded_worker()}.items():self.cfg.set(k,v)
            def load(self):return app
        Server().run()
if __name__=="__main__": cli()
elif 'gunicorn' in sys.modules and '--preload' not in sys.argv:start_embedded_worker()
