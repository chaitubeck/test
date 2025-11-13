Here is the fully updated Confluence-ready page, now including the additional long-term fix:
making Chat a separate microservice (instead of mixing it inside the main BFF).

This is written cleanly and professionally so you can paste it straight into Confluence.

⸻

🔧 Router/Proxy Latency & Chat Load Stabilization Plan

1. Overview

We are experiencing intermittent latency spikes and 499 errors during periods of elevated chat traffic. Key drivers include rapid chat polling, long-lived connections, slow upstream responses, long API Gateway timeouts, and multi-hop routing (Router → Proxy → BFF).

The following Immediate, Short-Term, and Long-Term actions will fully stabilize the system and create a scalable foundation.

⸻

2. Immediate Fix (Apply Today)

2.1 Increase Chat Polling Interval
	•	Increase chat polling from 3 seconds → 6 seconds.
	•	Instantly reduces chat traffic by ~50%.
	•	Helps router, proxy, and BFF maintain healthy connection pools.
	•	Prevents overlapping in-flight chat polls.

This is the only change required for immediate relief without infra or code deployments.

⸻

3. Short-Term Fixes (This Sprint)

Target: Prevent socket buildup, shorten stuck connections, and stabilize Router/Proxy under high chat volume.

⸻

3.1 Reduce NGINX Router & Proxy Timeouts

Recommended:

keepalive_timeout 5s;
proxy_connect_timeout 3s;
proxy_read_timeout 8s;
proxy_send_timeout 8s;

Avoids long-running connections that hog resources during chat delays.

⸻

3.2 Apply Chat-Specific Tight Timeout Overrides

location /frontendservice/.../onlineChat/ {
    proxy_read_timeout 4s;
    proxy_connect_timeout 2s;
}

Prevents slow chat endpoints from degrading the rest of the system.

⸻

3.3 Add DNS Resolver Stability (for OpenShift)

resolver dns-default.openshift-dns valid=10s ipv6=off;
resolver_timeout 2s;

Mitigates stale IP issues and DNS resolution delays introduced by recent OpenShift upgrades.

⸻

3.4 Adjust Router/Proxy Horizontal Scaling
	•	Maintain 8–12 Router pods for headroom.
	•	Increase Proxy pods if CPU or connection count spikes.
	•	Validate HPA sensitivity for latency and RPS.

⸻

3.5 Reduce API Gateway Timeouts (NEW)

Current timeout: 5 minutes → too long for polling endpoints.

Recommended:
	•	Reduce to 30 seconds or 1 minute.

Benefits:
	•	Frees sockets sooner.
	•	Reduces cascading delays.
	•	Prevents queue pile-ups during chat degradation.

Alignment between Router/Proxy vs Gateway timeouts significantly reduces CLOSE_WAIT accumulation.

⸻

4. Long-Term Fixes (Architecture)

Target: Remove systemic bottlenecks, decouple chat logic, and improve scalability.

⸻

4.1 Redesign Chat Through BFF (UI → Stateless)

UI should not manage Genesys session/chat IDs.

New model:
	•	BFF creates and owns Genesys session IDs.
	•	UI sends only:
	•	user identifier
	•	widget identifier
	•	message text

Benefits:
	•	Eliminates reconnect issues.
	•	Reduces UI traffic.
	•	Improves security.
	•	Enables WebSockets/SSE future adoption.

⸻

4.2 Make Chat a Dedicated Microservice (NEW)

Today chat logic lives inside the BFF alongside many unrelated features.
This creates tight coupling and forces the entire BFF to scale with chat load.

Recommendation:

Extract chat logic (Genesys integration, polling orchestration, session management) into a standalone microservice.

Benefits:
	•	Isolates the most high-volume component.
	•	Allows independent scaling during chat spikes.
	•	Reduces load on the main BFF.
	•	Cleaner separation of concerns (chat vs clinical/prescription features).
	•	Enables specialized caching, retry patterns, session stores for chat only.

This microservice becomes:

UI → Router → Chat-Service → Genesys Cloud
                          ↳ Chat-Session Cache (Redis)

The existing BFF becomes lighter and faster since chat is no longer interleaved with every patient/prescriber call.

⸻

4.3 Remove Proxy Layer (Router → BFF Direct)

Current:
Router → Proxy → BFF

Future:
Router → BFF (direct)

Benefits:
	•	Eliminates an entire hop.
	•	Removes redundant timeouts and connection pools.
	•	Simplifies routing and DNS.
	•	Less failure propagation.
	•	Substantial latency reduction.

⸻

5. Summary

Immediate
	•	Increase chat polling interval to 6 seconds.

Short-Term
	•	Reduce NGINX router/proxy timeouts.
	•	Add chat-specific timeout overrides.
	•	Add DNS resolver stability.
	•	Tune Router/Proxy scaling.
	•	Reduce API Gateway timeouts to 30–60s.

Long-Term
	•	Move chat session handling to BFF (UI stateless).
	•	Create a dedicated Chat Microservice.
	•	Remove the proxy layer (direct Router → BFF).

⸻

6. Next Steps

Item	Owner	Target Date
Increase chat polling interval to 6s	UI Team	Immediate
Update router/proxy timeouts	Platform	This sprint
Add resolver + chat-specific timeouts	Platform	This sprint
Reduce Gateway timeout from 5m → 30–60s	API Gateway Team	This sprint
Review Router/Proxy scaling thresholds	DevOps	This sprint
Redesign chat in BFF (UI stateless)	BFF Team	Q1
Create dedicated Chat Microservice	BFF + Architecture	Q1–Q2
Remove proxy layer	Platform + BFF	Q1–Q2


⸻

If you want, I can also generate:
	•	A visual architecture diagram showing current vs target
	•	A slide deck for leadership
	•	Or a risk matrix explaining what happens if we don’t implement these changes

Just tell me.
