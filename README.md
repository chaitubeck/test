Here is a clean, professional Confluence-ready page formatted exactly how engineering teams expect it — with clear sections, headings, bullets, and no unnecessary text.

You can copy/paste this directly into Confluence.

⸻

🔧 Router/Proxy Latency & Chat Load Stabilization Plan

1. Overview

We are currently observing intermittent latency spikes and 499 errors during high-load periods, especially driven by Genesys chat polling. Investigations show accumulated connections, timeout delays, and router/proxy queuing caused by rapid polling and long-lived sockets.

This page documents Immediate, Short-Term, and Long-Term fixes to fully stabilize the system.

⸻

2. Immediate Fix (Apply Today)

2.1 Increase Chat Polling Interval
	•	Increase chat polling from 3 seconds → 6 seconds.
	•	Provides an instant ~50% reduction in chat traffic.
	•	Reduces router and proxy connection pressure.
	•	Prevents overlapping polls and lowers cumulative socket buildup.

This is the only change required for immediate stability without code/infrastructure updates.

⸻

3. Short-Term Fixes (This Sprint)

Target: Reduce connection buildup, lower router/proxy queue time, and prevent polling endpoints from degrading the entire API.

3.1 Reduce NGINX Router & Proxy Timeouts

Shorter timeouts prevent sockets from staying open during slow chat responses.

Recommended settings:

keepalive_timeout 5s;
proxy_connect_timeout 3s;
proxy_read_timeout 8s;
proxy_send_timeout 8s;

3.2 Apply Chat-Specific Timeout Overrides

Protect the rest of the application from high-volume chat requests.

location /frontendservice/.../onlineChat/ {
    proxy_read_timeout 4s;
    proxy_connect_timeout 2s;
}

3.3 Add DNS Resolver for Stability

Prevents router/proxy from holding stale IPs and avoids intermittent DNS stalls.

resolver dns-default.openshift-dns valid=10s ipv6=off;
resolver_timeout 2s;

3.4 Review Router/Proxy Horizontal Scaling
	•	Maintain 8–12 router pods for traffic headroom.
	•	Scale proxy pods if CPU or active connection count rises under load.
	•	Review HPA thresholds for latency and RPS-based scaling.

⸻

4. Long-Term Fixes (Architectural Improvements)

Target: Remove structural bottlenecks, eliminate duplicate hops, and prevent recurrence under scale.

4.1 Redesign Chat Through BFF (Stateless UI)

Goal: UI should not manage Genesys session/chat IDs.

New Model:
	•	BFF owns all chat session IDs, tokens, and Genesys conversations.
	•	UI provides only user identifiers and widget IDs.
	•	BFF manages:
	•	session creation
	•	session lookup
	•	message polling
	•	session termination

Benefits:
	•	Removes reconnect issues and UI-driven session churn.
	•	Reduces the number of chat requests needed.
	•	Simplifies UI and decreases traffic load.
	•	Provides better security and observability.
	•	Enables easy migration to WebSockets/SSE.

⸻

4.2 Remove Proxy Layer

Current flow:
Router → Proxy → BFF → Downstream APIs

Target flow:
Router → BFF (direct)

Benefits:
	•	Eliminates an entire hop (lower latency).
	•	Removes duplicated timeouts/connection pools.
	•	Avoids double DNS resolution.
	•	Simplifies routing logic.
	•	Reduces risk of socket buildup and 499 propagation.
	•	Cleaner architecture for future features and scale.

⸻

5. Summary

Immediate
	•	Increase chat polling interval to 6 seconds.

Short-Term
	•	Reduce router/proxy timeouts.
	•	Add chat-specific timeouts.
	•	Add DNS resolver stability.
	•	Ensure proper router/proxy scaling.

Long-Term
	•	Move chat session management to BFF (stateless UI).
	•	Remove proxy layer and route Router → BFF directly.

⸻

6. Next Steps

Item	Owner	Target Date
Increase chat polling interval to 6s	UI Team	Immediate
Update router/proxy timeouts	Platform	This sprint
Add resolver + timeout overrides	Platform	This sprint
Review scaling + HPA	DevOps	This sprint
Chat redesign (BFF-managed state)	BFF Team	Q1
Remove proxy & refactor routing	Platform + BFF	Q1–Q2


⸻

If you’d like, I can also generate a slide deck version for leadership or a flow diagram showing the “Current vs Target Architecture.”
