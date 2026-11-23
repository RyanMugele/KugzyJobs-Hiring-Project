import os
bind = "0.0.0.0:" + os.environ.get("PORT", "10000")
# One process keeps memory and SQLite write contention modest for the project demo.
workers = 1
worker_class = "sync"
timeout = 120
accesslog = "-"
errorlog = "-"
# ProxyFix trusts only the forwarded protocol, explicitly enabled in render.yaml.
forwarded_allow_ips = ""
