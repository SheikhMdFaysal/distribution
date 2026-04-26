"""RQ worker entry point — invoked by .claude/launch.json"""
import sys
sys.argv = ["rq", "worker", "--url", "redis://localhost:6379/0"]

from rq.cli import main
main()
