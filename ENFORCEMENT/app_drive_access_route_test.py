#!/usr/bin/env python3
"""Regression for service-only Drive routing. No cloud calls or mutations."""
from pathlib import Path
import importlib.util
p=Path(__file__).with_name("app_drive_access_route.py")
s=importlib.util.spec_from_file_location("route",p)
m=importlib.util.module_from_spec(s)
s.loader.exec_module(m)

safe=[{"type":"user","role":"owner","emailAddress":"owner@example.invalid"}]
unsafe=[{"type":"anyone","role":"writer"},{"type":"user","role":"owner"}]
public_reader=[{"type":"anyone","role":"reader"},{"type":"user","role":"owner"}]
def blocked(reason, action, **opts):
    try: m.plan_app_operation(action,**opts)
    except m.RouteBlocked as err: assert str(err)==reason,(reason,str(err));return
    raise AssertionError("Expected "+reason)
base={"caller":"TRUSTED_APP_BACKEND","verified_identity":True,"owner_user_id":"test-user","owner_scope_verified":True,"acl_permissions":safe}
for name in ("HOMEWORK_READ","HOMEWORK_WRITE","HOMEWORK_UPLOAD","LEARNING_EVIDENCE_WRITE","USER_RECORD_READ","USER_RECORD_WRITE","FAMILY_SHARE_MANAGE"):
    r=m.plan_app_operation(name,**base)
    assert r["storage_account"]=="SIEZEALL",r
    assert r["role"]=="04_USER_DATA",r
    assert r["no_direct_drive_client"] is True
    assert r["route_state"]=="SERVER_SIDE_PLAN_ONLY_NOT_ACCESS_AUTHORIZATION"
    assert r["drive_folder_id"]=="1basjn1lv8YTyo0MMMRHBKCmRv5jWyqUf"
blocked("USER_DIRECT_DRIVE_FORBIDDEN","HOMEWORK_WRITE",**{**base,"caller":"USER"})
blocked("APP_IDENTITY_UNVERIFIED","HOMEWORK_WRITE",**{**base,"verified_identity":False})
blocked("USER_SCOPE_UNVERIFIED","HOMEWORK_WRITE",**{**base,"owner_scope_verified":False})
blocked("ACL_READBACK_REQUIRED","HOMEWORK_WRITE",**{**base,"acl_permissions":None})
blocked("UNSAFE_PUBLIC_DRIVE_ACL","HOMEWORK_WRITE",**{**base,"acl_permissions":unsafe})
blocked("UNSAFE_PUBLIC_DRIVE_ACL","HOMEWORK_READ",**{**base,"acl_permissions":public_reader})
blocked("UNKNOWN_ACTION","GOOGLE_DRIVE_BROWSE",**base)
content=m.plan_app_operation("CONTENT_CATALOG_READ",caller="TRUSTED_APP_BACKEND",verified_identity=True,acl_permissions=safe)
assert content["role"]=="03_UPDATES" and content["storage_account"]=="SIEZEALL"
assert content["drive_folder_id"]=="111nmMqJvFfwKYoxaKBGmJWWMoqvCck0s"
blocked("UNSAFE_PUBLIC_DRIVE_ACL","CONTENT_PACKAGE_PUBLISH",caller="TRUSTED_APP_BACKEND",verified_identity=True,approved_operator=True,acl_permissions=unsafe)
blocked("OPERATOR_AUTHORITY_REQUIRED","CONTENT_PACKAGE_PUBLISH",caller="TRUSTED_APP_BACKEND",verified_identity=True,acl_permissions=safe)
admin=m.plan_app_operation("OPERATION_CONFIG_READ",caller="TRUSTED_APP_BACKEND",verified_identity=True,approved_operator=True,acl_permissions=safe)
assert admin["storage_account"]=="HNS" and admin["role"]=="03_COMMON"
master=m.plan_app_operation("APPROVED_VISUAL_MASTER_READ",caller="TRUSTED_APP_BACKEND",verified_identity=True,approved_operator=True,acl_permissions=safe)
assert master["storage_account"]=="HNS" and master["role"]=="UI_SOURCE_AUTHORITY"
assert master["drive_folder_id"]=="10CJIHS_SEs_u79tj7z4FcZFPICfLuPVA"
print("APP_DRIVE_ACCESS_ROUTE_TEST: PASS (service-only, stable IDs, ACL fail-closed, cross-role)")
