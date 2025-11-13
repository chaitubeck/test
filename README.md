Here is the single unified table (Confluence-ready) with Finding → Description → Fix Type → Recommended Fix all in the same row.

You can copy–paste this directly into Confluence.
(This is the cleanest and easiest version for leadership + engineering.)

⸻

✅ Unified Table: Findings, Description, Fix Type, Recommended Fix

Finding	Description	Fix Type	Recommended Fix
High chat polling frequency (2–3s)	UI hits chat APIs too frequently, causing overlapping in-flight requests and router/proxy backpressure.	Immediate	Increase polling interval from 3s → 6s (cuts load ~50%).
Proxy → BFF bottleneck	Proxy adds an extra hop; under load it holds open connections and times out.	Short-Term	Reduce proxy/router timeouts, consider early connection cleanup.
Long router/proxy/BFF timeouts	30–300s timeouts keep sockets open, causing CLOSE_WAIT buildup.	Short-Term	Set router/proxy timeouts: connect=3s, read=8s, send=8s, keepalive=5s.
Chat endpoints not having specific timeout rules	Chat APIs behave differently from other endpoints but share the same slow timeouts.	Short-Term	Apply chat-specific overrides (e.g., read_timeout=4s, connect_timeout=2s).
API Gateway timeout too long (5 mins)	Very long gateway timeouts allow stuck calls to survive for minutes and overwhelm connection pools.	Short-Term	Reduce API Gateway timeout from 5 minutes → 30–60 seconds.
OpenShift DNS stale IP caching	Router may retain old pod IPs after OpenShift recent upgrades (Whereabouts changes).	Short-Term	Add resolver: dns-default.openshift-dns valid=10s; resolver_timeout 2s;.
Router/Proxy scaling not aligned with chat spikes	Chat surges cause sudden bursts; default 8–10 pods may be insufficient during peak concurrency.	Short-Term	Increase router/proxy HPA limits, validate scaling triggers by RPS/latency.
Chat service tightly coupled inside BFF	Chat logic lives inside the main BFF, forcing entire BFF to scale with chat traffic.	Long-Term	Extract Chat Microservice with dedicated scaling + caching (Redis).
UI stores chat/session IDs (stateful)	UI keeps Genesys chat session IDs, causing retry storms and extra load.	Long-Term	Make UI stateless; BFF generates + manages session IDs (UI → BFF only).
Proxy layer adds unnecessary overhead	Router → Proxy → BFF creates additional latency, DNS lookup, TLS handshake.	Long-Term	Remove proxy hop and route directly from Router → BFF.
No dedicated chat compute isolation	Chat competes with prescription, user, and CMS APIs inside the same BFF pods.	Long-Term	Create separate Chat Service with its own HPA, connection pools, and retry logic.


⸻

✅ This is the COMPLETE table—no other tables required.

If you want, I can also generate:
	•	✔ A Confluence layout with headers + collapsible sections
	•	✔ A leadership-ready slide deck
	•	✔ A current vs target architecture diagram
	•	✔ A problem-impact-solution matrix

Just tell me what you want next.
