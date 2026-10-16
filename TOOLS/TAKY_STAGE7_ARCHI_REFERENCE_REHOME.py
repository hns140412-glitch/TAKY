"""RETIRED one-off rehome entrypoint; read-only compatibility guard.
The physical reference authority is now TAKY-SOURCE-VAULT/REFERENCE.
The legacy Stage7 source is preserved under WORKBENCH/90_ARCHIVE.
"""
import argparse,json,sys
from pathlib import Path
import TAKY_REFERENCE_SINGLE_SOURCE_REHOME as authority
def main():
 parser=argparse.ArgumentParser()
 group=parser.add_mutually_exclusive_group(required=True)
 group.add_argument("--audit",action="store_true")
 group.add_argument("--apply",action="store_true")
 args=parser.parse_args()
 result=authority.check_applied()
 result["legacy_stage7_move_disabled"]=True
 result["requested_apply_was_read_only"]=bool(args.apply)
 result["physical_reference_authority"]=str(authority.TARGET)
 print(json.dumps(result,ensure_ascii=False))
 return 0
if __name__=="__main__":sys.exit(main())
