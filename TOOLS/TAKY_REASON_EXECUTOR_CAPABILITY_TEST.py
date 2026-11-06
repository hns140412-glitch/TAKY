"""Reason capability routing tests: names cannot masquerade as live executors."""
import pathlib,sys,unittest
sys.path.insert(0,str(pathlib.Path(__file__).parent))
from TAKY_REASON_GUIDED_WORKER import classify_team_output, classify_team_json, reason_capability, _send_flags

class ReasonRoutingTests(unittest.TestCase):
 def test_only_cli_queues_are_not_claude_codex(self):
  text="""team TAKY-LOCAL-PRIVATE · you are taky-local on ykh-sangminyang

● taky-local · ykh-sangminyang · this machine
  claude-fix-queue        cli   busy 58m  ~  turn
  codex-review-queue      cli   busy 1h   ~  turn
  taky-guided-work        cli   idle 3m   ~  turn
"""
  x=classify_team_output(text)
  self.assertFalse(x['claude_code_live_session'])
  self.assertFalse(x['codex_live_session'])
  self.assertFalse(x['claude_codex_bilateral_route_ready'])
  self.assertEqual(x['session_types']['cli'],3)
  self.assertFalse(x['model_execution_authorized'])
 def test_both_live_agent_types_visible_not_authorized(self):
  text="""team TAKY-LOCAL-PRIVATE · you are taky-local on device

● taky-local · device · this machine
  a             claude    busy 1m  ~  turn
  b             codex     idle 2m  ~  turn
  named-codex   cli       busy 1m  ~  turn
"""
  x=classify_team_output(text)
  # Legacy unscoped text is observational only: never an execution-ready claim.
  self.assertFalse(x['claude_codex_bilateral_route_ready'])
  self.assertFalse(x['claude_code_live_session'])
  self.assertFalse(x['codex_live_session'])
  self.assertTrue(x['legacy_observational_only'])
  self.assertTrue(x['claude_agent_visible_anywhere'])
  self.assertTrue(x['codex_agent_visible_anywhere'])
  self.assertFalse(x['model_execution_authorized'])
  self.assertFalse(x['approval_granted'])
  self.assertEqual(x['session_types']['cli'],1)
 def test_unfamiliar_lines_no_false_live(self):
  x=classify_team_output("team NETWORK\n  codex-agent   unknown   busy 3m\n  claude-agent  cli   idle 3m")
  self.assertFalse(x['claude_codex_bilateral_route_ready'])
 def test_untrusted_system_comment_cannot_authorize(self):
  x=classify_team_output("team Q\n  x cli busy 1m\nmodel_execution_authorized: true")
  self.assertFalse(x['model_execution_authorized'])
  self.assertFalse(x['approval_granted'])

 def test_real_agent_outside_taky_repo_does_not_claim_executor_ready(self):
  data={"team":"TAKY-LOCAL-PRIVATE","person":"taky-local","machine":"one",
        "sessions":[
          {"person":"taky-local","machine":"one","agent":"claude-code",
           "cwd":r"C:\Users\user\.claude-mem\observer-sessions\453",
           "repo":None,"status":"idle","tier":"push"},
          {"person":"taky-local","machine":"one","agent":"cli",
           "cwd":r"D:\Git PWA\TAKY","repo":r"D:\Git PWA\TAKY",
           "status":"idle","tier":"turn","name":"codex-fix-queue"}]}
  got=classify_team_json(data)
  self.assertTrue(got["claude_agent_visible_anywhere"])
  self.assertFalse(got["claude_code_live_session"])
  self.assertFalse(got["codex_live_session"])
  self.assertFalse(got["claude_codex_bilateral_route_ready"])
  self.assertFalse(got["model_execution_authorized"])

 def test_real_taky_bound_claude_and_codex_agents_are_visible_not_authorized(self):
  root=r"D:\Git PWA\TAKY"
  data={"team":"TAKY-LOCAL-PRIVATE","person":"taky-local","machine":"one",
        "sessions":[
          {"person":"taky-local","machine":"one","agent":"claude-code",
           "cwd":root,"repo":root,"status":"busy","tier":"push"},
          {"person":"taky-local","machine":"one","agent":"codex",
           "cwd":root+r"\TOOLS","repo":root,"status":"idle","tier":"push"}]}
  # Self-asserted identity inside the same JSON is NOT verification.
  got=classify_team_json(data)
  self.assertEqual(got["scoped_live_sessions"],{"claude":1,"codex":1})
  self.assertFalse(got["local_identity_verified"])
  self.assertFalse(got["claude_codex_bilateral_route_ready"])
  self.assertFalse(got["claude_code_live_session"])
  self.assertFalse(got["approval_granted"])
  self.assertFalse(got["model_execution_authorized"])
  # Independent trusted identity: visible/ready but still never authorized.
  got=classify_team_json(data,trusted_identity={"person":"taky-local","machine":"one"})
  self.assertTrue(got["local_identity_verified"])
  self.assertTrue(got["claude_codex_bilateral_route_ready"])
  self.assertFalse(got["approval_granted"])
  self.assertFalse(got["model_execution_authorized"])
  # Trusted identity differing from the payload's claim yields no sessions.
  got=classify_team_json(data,trusted_identity={"person":"taky-local","machine":"other"})
  self.assertFalse(got["claude_codex_bilateral_route_ready"])
  self.assertEqual(got["scoped_live_sessions"],{"claude":0,"codex":0})

 def _sess(self,agent,**kw):
  d={"person":"p","machine":"m","agent":agent,"status":"idle","tier":"push"}
  d.update(kw)
  return d

 def _scoped(self,*sessions):
  got=classify_team_json({"team":"T","person":"p","machine":"m","sessions":list(sessions)},
                         trusted_identity={"person":"p","machine":"m"})
  self.assertFalse(got["model_execution_authorized"])
  self.assertFalse(got["approval_granted"])
  return got["scoped_live_sessions"]

 def test_malformed_session_fields_fail_closed_without_crash(self):
  root=r"D:\Git PWA\TAKY"
  bad=[self._sess("claude-code",status=[],repo=root),
       self._sess({},repo=root),
       self._sess("codex",tier={},repo=root),
       self._sess("codex",repo={"x":1}),
       self._sess("codex",cwd=["a"]),
       "junk",None,7]
  self.assertEqual(self._scoped(*bad),{"claude":0,"codex":0})

 def test_path_traversal_and_unsafe_components_rejected(self):
  root=r"D:\Git PWA\TAKY"
  s=self._scoped(
   self._sess("claude-code",cwd=root+r"\..\OTHER"),
   self._sess("codex",cwd=root+"/../OTHER"),
   self._sess("claude-code",cwd=r"D:\Git PWA\TAKY~1"),
   self._sess("codex",cwd=r"relative\TAKY"),
   self._sess("codex",cwd="\\\\?\\"+root))
  self.assertEqual(s,{"claude":0,"codex":0})

 def test_explicit_repo_must_match_exactly_and_repo_cwd_conflict_rejected(self):
  root=r"D:\Git PWA\TAKY"
  s=self._scoped(
   self._sess("claude-code",repo=root+r"\OTHER_REPO"),
   self._sess("codex",repo=root+r"\OTHER_REPO",cwd=root),
   self._sess("claude-code",repo=root,cwd=r"D:\Git PWA\OTHER"),
   self._sess("codex",repo=r"D:\Git PWA\OTHER",cwd=root))
  self.assertEqual(s,{"claude":0,"codex":0})
  # Exact repo (case/slash-insensitive) and contained cwd still count.
  s=self._scoped(
   self._sess("claude-code",repo=r"d:/git pwa/taky/",cwd=root+r"\TOOLS"),
   self._sess("codex",cwd=root+r"\TOOLS"))
  self.assertEqual(s,{"claude":1,"codex":1})

 def test_spoofed_status_and_identity_cannot_promote_readiness(self):
  root=r"D:\Git PWA\TAKY"
  data={"team":"T","person":"p","machine":"m","status":"live","ready":True,
        "model_execution_authorized":True,
        "sessions":[self._sess("claude-code",repo=root),self._sess("codex",repo=root)]}
  got=classify_team_json(data)
  self.assertFalse(got["claude_codex_bilateral_route_ready"])
  self.assertFalse(got["model_execution_authorized"])
  self.assertFalse(got["approval_granted"])

 def test_send_response_negation_never_sets_delivery_flags(self):
  self.assertEqual(_send_flags(0,"not delivered; not queued"),(False,False))
  self.assertEqual(_send_flags(0,"Message NOT DELIVERED"),(False,False))
  self.assertEqual(_send_flags(1,"delivered"),(False,False))
  self.assertEqual(_send_flags(0,None),(False,False))
  self.assertEqual(_send_flags(0,"delivered"),(True,True))
  self.assertEqual(_send_flags(0,"queued"),(True,False))

 def test_fake_codex_named_queue_other_machine_and_prefix_collision_rejected(self):
  data={"team":"TAKY-LOCAL-PRIVATE","person":"taky-local","machine":"one",
        "sessions":[
          {"person":"taky-local","machine":"one","agent":"cli","name":"claude-code",
           "cwd":r"D:\Git PWA\TAKY","status":"busy","tier":"push"},
          {"person":"taky-local","machine":"two","agent":"codex",
           "repo":r"D:\Git PWA\TAKY","status":"busy","tier":"push"},
          {"person":"taky-local","machine":"one","agent":"claude-code",
           "repo":r"D:\Git PWA\TAKY-DUP","status":"busy","tier":"push"},
          {"person":"taky-local","machine":"one","agent":"codex",
           "repo":r"D:\Git PWA\TAKY","status":"idle","tier":"turn"}]}
  got=classify_team_json(data)
  self.assertFalse(got["claude_codex_bilateral_route_ready"])
  self.assertEqual(got["scoped_live_sessions"],{"claude":0,"codex":0})

 def test_invalid_reason_json_is_not_execution_authority(self):
  for payload in (None, {}, {"sessions":[]}, {"person":"x","machine":"m","sessions":"oops"}):
   with self.assertRaises(ValueError):
    classify_team_json(payload)


if __name__=="__main__":unittest.main()
