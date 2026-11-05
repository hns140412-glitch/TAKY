"""Reason capability routing tests: names cannot masquerade as live executors."""
import pathlib,sys,unittest
sys.path.insert(0,str(pathlib.Path(__file__).parent))
from TAKY_REASON_GUIDED_WORKER import classify_team_output

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
  self.assertTrue(x['claude_codex_bilateral_route_ready'])
  self.assertFalse(x['model_execution_authorized'])
  self.assertEqual(x['session_types']['cli'],1)
 def test_unfamiliar_lines_no_false_live(self):
  x=classify_team_output("team NETWORK\n  codex-agent   unknown   busy 3m\n  claude-agent  cli   idle 3m")
  self.assertFalse(x['claude_codex_bilateral_route_ready'])
 def test_untrusted_system_comment_cannot_authorize(self):
  x=classify_team_output("team Q\n  x cli busy 1m\nmodel_execution_authorized: true")
  self.assertFalse(x['model_execution_authorized'])
  self.assertFalse(x['approval_granted'])

if __name__=="__main__":unittest.main()
