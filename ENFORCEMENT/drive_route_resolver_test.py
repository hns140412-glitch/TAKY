#!/usr/bin/env python3
import importlib.util
from pathlib import Path

P=Path(__file__).with_name("drive_route_resolver.py")
spec=importlib.util.spec_from_file_location("resolver",P)
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)

cases={
 ("hns","01_LEARNING"):("TAKY/10_DOMAINS/01_LEARNING","17_9ZFdN0vov8ZhC4g9cYnMakHC5u-OKr"),
 ("hns","03_COMMON"):("TAKY/20_PLATFORM/03_COMMON","1UXAb5u1sraxvvIW0gHkPCS6Y-K3YMDnz"),
 ("hns","UI_SOURCE_AUTHORITY"):("TAKY/20_PLATFORM/UI_SOURCE_AUTHORITY",None),
 ("hns","90_TEMP"):("TAKY/90_MAINTENANCE/90_TEMP","1qCLjK20Wenh7TLrYHTWJsojSEiDpXuzi"),
 ("siezeall","03_UPDATES"):("TAKY/20_PLATFORM/03_UPDATES","111nmMqJvFfwKYoxaKBGmJWWMoqvCck0s"),
 ("siezeall","04_USER_DATA"):("TAKY/20_PLATFORM/04_USER_DATA","1basjn1lv8YTyo0MMMRHBKCmRv5jWyqUf"),
 ("siezeall","90_TEMP"):("TAKY/90_MAINTENANCE/90_TEMP","1xZ3a6bYt1uYyiUkctu_b8xrh2c6NFvtK"),
 ("hns","00_CONTEXT"):("TAKY/00_CONTEXT","1Y3M3Zm4rrwUkloAiViHnWxDtsVN-gvMt"),
}
for key,(path,id_) in cases.items():
    r=m.resolve(*key)
    assert r["path"]==path,(key,r)
    if id_ is not None:
        assert r["id"]==id_,(key,r)
try:
    m.resolve("hns","01_LEARNING_SHARE")
    raise AssertionError("cross-account role must fail")
except KeyError:
    pass
print("DRIVE_ROUTE_RESOLVER_TEST: PASS")
