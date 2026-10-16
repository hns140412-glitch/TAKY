#!/usr/bin/env python3
"""Read-only Netlify account credit capability collector.

A monthly plan remainder is NOT necessarily the available team balance:
purchased/rollover/promotional credits may be excluded. Never report the
monthly difference as the real Credit balance ledger.
"""
import datetime as dt
import json
from pathlib import Path
import urllib.request
import urllib.error
import time

TEAM_SLUGS = ("hns140412", "siezeall-w0pgkzo")
INTERVAL = 3600

def account_credit_fields(raw, slug, now=None):
    if not isinstance(raw, dict) or str(raw.get("slug","")) != slug:
        raise ValueError("ACCOUNT_IDENTITY_MISMATCH")
    capability = raw.get("capabilities") or {}
    credits = capability.get("credits") if isinstance(capability,dict) else None
    record={"slug":slug,"source":"netlify_official_accounts_api",
            "observedAt":dt.datetime.fromtimestamp(now or time.time(),dt.timezone.utc).isoformat(),
            "creditBalanceAvailable":None,"monthlyIncluded":None,"monthlyUsed":None,
            "monthlyIncludedRemaining":None,"scope":"TEAM_ACCOUNT","balanceSource":"NOT_PROVIDED"}
    if isinstance(credits, dict):
        included,used=credits.get("included"),credits.get("used")
        if (isinstance(included,(float,int)) and not isinstance(included,bool)
            and isinstance(used,(float,int)) and not isinstance(used,bool)
            and 0<=included<=1e9 and 0<=used<=1e9):
            record.update(monthlyIncluded=included,monthlyUsed=used,
                          monthlyIncludedRemaining=max(0,round(included-used,2)),
                          balanceSource="MONTHLY_CAPABILITY_ONLY")
    return record

def fetch(slug,token,fetcher=None):
    if slug not in TEAM_SLUGS: raise ValueError("UNKNOWN_TEAM")
    if not isinstance(token,str) or not 16<=len(token)<=512:
        raise ValueError("INVALID_TOKEN_FORMAT")
    request=urllib.request.Request(
        "https://api.netlify.com/api/v1/accounts/"+slug,
        method="GET",
        headers={"Authorization":"Bearer "+token,
                 "Accept":"application/json","User-Agent":"TAKY-Usage-ReadOnly/1.0"})
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self,*args):return None
    reader=fetcher or urllib.request.build_opener(NoRedirect()).open
    with reader(request,timeout=9) as resp:
        payload=json.loads(resp.read(100_000))
    return account_credit_fields(payload,slug)

def tests():
    import unittest
    from unittest.mock import Mock
    class Cases(unittest.TestCase):
        def test_capability_and_separate_balance(self):
            r=account_credit_fields({"slug":"hns140412",
                 "capabilities":{"credits":{"included":500,"used":81.3}}},
                 "hns140412",now=1000)
            self.assertEqual(r["monthlyIncludedRemaining"],418.7)
            self.assertIsNone(r["creditBalanceAvailable"])
            self.assertEqual(r["balanceSource"],"MONTHLY_CAPABILITY_ONLY")
        def test_missing_is_never_zero(self):
            r=account_credit_fields({"slug":"hns140412",
                 "capabilities":{}},"hns140412",now=1000)
            self.assertIsNone(r["monthlyIncludedRemaining"])
            self.assertIsNone(r["creditBalanceAvailable"])
        def test_team_mismatch_block(self):
            with self.assertRaises(ValueError):
                account_credit_fields({"slug":"another-team",
                  "capabilities":{"credits":{"included":999999,"used":0}}},
                  "hns140412")
        def test_readonly_url_and_no_credentials_in_result(self):
            token="TEST_TOKEN_NOT_REAL_"+"x"*30
            calls=[]
            class R:
                def __enter__(self):return self
                def __exit__(self,*args):pass
                def read(self,limit):return b'{"slug":"hns140412","capabilities":{"credits":{"included":500,"used":1}}}'
            def reader(req,timeout):
                self.assertEqual(req.get_method(),"GET")
                self.assertEqual(req.full_url,"https://api.netlify.com/api/v1/accounts/hns140412")
                calls.append(1)
                return R()
            r=fetch("hns140412",token,fetcher=reader)
            self.assertEqual(len(calls),1)
            self.assertNotIn(token,json.dumps(r))
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(Cases)
    return unittest.TextTestRunner(verbosity=1).run(suite).wasSuccessful()

if __name__=="__main__":
    raise SystemExit(0 if tests() else 1)
