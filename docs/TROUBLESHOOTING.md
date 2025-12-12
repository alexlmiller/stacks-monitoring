# Troubleshooting

Common issues and solutions for the Stacks monitoring stack.

## Metrics Issues

### No metrics appearing in Grafana

**Symptoms:**
- Dashboard shows "No data"
- Prometheus/VictoriaMetrics queries return empty

**Checklist:**

1. **Verify targets are up**
   ```bash
   # Check Alloy targets
   curl -s http://localhost:12345/api/v0/component/prometheus.scrape.stacks_node/targets | jq .
   ```

2. **Test metric endpoints directly**
   ```bash
   # Stacks node
   curl -s http://localhost:9153/metrics | head

   # Signer
   curl -s http://localhost:30001/metrics | head

   # Bitcoin
   curl -s http://localhost:9332/metrics | head
   ```

3. **Check remote write connectivity**
   ```bash
   # VictoriaMetrics
   curl -s http://monitoring-hub:8428/api/v1/status/tsdb

   # Test write
   curl -X POST http://monitoring-hub:8428/api/v1/import/prometheus \
     -d 'test_metric{job="test"} 1'
   ```

4. **Verify labels match dashboard variables**
   ```promql
   # Check what labels exist
   up{job=~".*stacks.*"}
   ```

### Metrics are delayed

**Symptoms:**
- Data appears minutes behind real-time
- Gaps in graphs

**Solutions:**

1. **Check scrape interval**
   ```alloy
   prometheus.scrape "stacks_node" {
     scrape_interval = "15s"  // Reduce if needed
   }
   ```

2. **Check remote write batching**
   ```alloy
   prometheus.remote_write "default" {
     queue_config {
       max_samples_per_send = 1000
       batch_send_deadline  = "5s"  // Reduce for faster sends
     }
   }
   ```

3. **Verify clock sync**
   ```bash
   timedatectl status
   ntpq -p
   ```

### High cardinality warnings

**Symptoms:**
- VictoriaMetrics/Prometheus warns about cardinality
- Query performance degrades

**Solutions:**

1. **Identify high-cardinality metrics**
   ```promql
   # Top metrics by series count
   topk(10, count by (__name__)({__name__!=""}))
   ```

2. **Drop unnecessary labels**
   ```alloy
   prometheus.relabel "drop_high_cardinality" {
     rule {
       action       = "labeldrop"
       regex        = "transaction_id|peer_address"
     }
   }
   ```

## Log Issues

### Logs not appearing

**Symptoms:**
- No logs in Grafana Explore
- Loki/VictoriaLogs queries return empty

**Checklist:**

1. **Verify Alloy can read logs**
   ```bash
   # For journal
   docker exec stacks-alloy-agent journalctl -u stacks-node -n 5

   # For files
   docker exec stacks-alloy-agent ls -la /var/log/
   ```

2. **Check Alloy pipeline status**
   ```bash
   curl -s http://localhost:12345/api/v0/component/loki.source.journal.stacks/targets
   ```

3. **Test log endpoint**
   ```bash
   # VictoriaLogs
   curl -s 'http://monitoring-hub:9428/select/logsql/query?query=*' | head

   # Loki
   curl -s 'http://monitoring-hub:3100/loki/api/v1/labels'
   ```

4. **Verify stream fields (VictoriaLogs)**
   ```bash
   # Should include job, host, service, level
   curl -s 'http://monitoring-hub:9428/select/logsql/streams'
   ```

### Level extraction not working

**Symptoms:**
- All logs show without `level` label
- Can't filter by `level="error"`

**Solutions:**

1. **Verify log format matches regex**
   ```bash
   # Check actual log format
   journalctl -u stacks-node -o short-precise -n 5

   # Expected: INFO [timestamp] [file:line] message
   ```

2. **Test regex manually**
   ```bash
   echo 'INFO [1234.5] [src/main.rs:42] test message' | \
     grep -oP '^(?P<level>\w+)\s+\['
   ```

3. **Check pipeline order in Alloy config**
   - Level extraction must happen before `loki.write`

### Log volume too high

**Symptoms:**
- Disk filling quickly
- Alloy using high memory/CPU

**Solutions:**

1. **Add sampling for verbose services**
   ```alloy
   loki.process "sample_verbose" {
     stage.sampling {
       rate = 0.1  // Keep 10%
     }
   }
   ```

2. **Filter out noise**
   ```alloy
   stage.drop {
     expression = ".*(heartbeat|ping|health).*"
     drop_counter_reason = "noise"
   }
   ```

3. **Increase log retention limits**
   ```bash
   # VictoriaLogs
   --retentionPeriod=7d
   --storage.maxDiskSpace=50GB
   ```

## Alert Issues

### Alerts not firing

**Symptoms:**
- Known issues exist but no alerts
- Alert rules show as "inactive"

**Checklist:**

1. **Verify alert rules loaded**
   ```bash
   # Prometheus
   curl -s http://monitoring-hub:9090/api/v1/rules | jq '.data.groups[].rules[] | select(.name | contains("Stacks"))'

   # Grafana
   curl -s http://monitoring-hub:3000/api/v1/provisioning/alert-rules | jq '.[].title'
   ```

2. **Check evaluation errors**
   ```bash
   # Prometheus alerts page
   curl -s http://monitoring-hub:9090/api/v1/alerts | jq '.data.alerts[] | select(.state == "error")'
   ```

3. **Test alert conditions manually**
   ```promql
   # Should return results if alert should fire
   stacks_signer_is_registered == 0
   up{service="stacks-signer"} == 0
   ```

### Too many alerts

**Symptoms:**
- Alert fatigue
- Flapping alerts

**Solutions:**

1. **Adjust thresholds**
   ```yaml
   # Increase for duration
   for: 5m  # Wait 5 minutes before firing
   ```

2. **Add inhibition rules**
   ```yaml
   # Don't alert signer issues if node is down
   inhibit_rules:
     - source_match:
         alertname: StacksNodeDown
       target_match:
         alertname: StacksSignerNotRegistered
   ```

3. **Group alerts**
   ```yaml
   route:
     group_by: ['alertname', 'host']
     group_wait: 30s
     group_interval: 5m
   ```

## Connection Issues

### Alloy can't reach targets

**Symptoms:**
- Targets show as "down"
- Connection refused errors

**Solutions:**

1. **Docker networking**
   ```yaml
   # Add to docker-compose for Linux
   extra_hosts:
     - "host.docker.internal:host-gateway"
   ```

2. **Firewall rules**
   ```bash
   # Check if ports are accessible
   nc -zv localhost 9153
   nc -zv localhost 30001
   nc -zv localhost 9332
   ```

3. **Service binding**
   ```bash
   # Verify services listen on expected interfaces
   netstat -tlnp | grep -E '9153|30001|9332'

   # Should show 0.0.0.0 or specific IP, not just 127.0.0.1
   ```

### Remote write failures

**Symptoms:**
- "remote write: connection refused" in logs
- Metrics not reaching storage

**Solutions:**

1. **Verify endpoint URL**
   ```bash
   # Test connectivity
   curl -v http://monitoring-hub:8428/api/v1/write

   # Should return 200 or 204 for empty write
   ```

2. **Check DNS resolution**
   ```bash
   nslookup monitoring-hub
   dig monitoring-hub
   ```

3. **Verify TLS if used**
   ```bash
   # Test with openssl
   openssl s_client -connect monitoring-hub:443
   ```

## Performance Issues

### High memory usage

**Symptoms:**
- Alloy OOM kills
- Container restarts

**Solutions:**

1. **Reduce batch sizes**
   ```alloy
   prometheus.remote_write "default" {
     queue_config {
       capacity          = 2500
       max_shards        = 4
       max_samples_per_send = 500
     }
   }
   ```

2. **Limit log buffer**
   ```alloy
   loki.source.journal "stacks" {
     max_age = "1h"  // Don't buffer too much history
   }
   ```

3. **Increase container limits**
   ```yaml
   deploy:
     resources:
       limits:
         memory: 1G  # Increase from 512M
   ```

### Slow dashboard loading

**Symptoms:**
- Grafana queries timeout
- Dashboards take 10+ seconds

**Solutions:**

1. **Add recording rules**
   ```yaml
   - record: stacks:signer_rejection_rate:5m
     expr: rate(stacks_signer_block_responses_sent{response_type="rejected"}[5m]) / rate(stacks_signer_block_responses_sent[5m])
   ```

2. **Reduce time range**
   - Default to 1h or 6h instead of 24h

3. **Optimize queries**
   ```promql
   # Before (slow)
   sum(rate(metric[5m])) by (host)

   # After (faster with filter)
   sum(rate(metric{job="stacks"}[5m])) by (host)
   ```

## Debug Commands

### Alloy Debug

```bash
# Component status
curl -s http://localhost:12345/api/v0/web/components | jq .

# Specific component
curl -s http://localhost:12345/api/v0/component/prometheus.scrape.stacks_node

# Pipeline graph
open http://localhost:12345/graph
```

### VictoriaMetrics Debug

```bash
# Active queries
curl http://localhost:8428/api/v1/status/active_queries

# TSDB status
curl http://localhost:8428/api/v1/status/tsdb

# Cardinality
curl http://localhost:8428/api/v1/status/tsdb | jq '.data.totalSeries'
```

### VictoriaLogs Debug

```bash
# Stream list
curl 'http://localhost:9428/select/logsql/streams?limit=100'

# Recent logs
curl 'http://localhost:9428/select/logsql/query?query=_time:5m'

# Stats
curl http://localhost:9428/metrics | grep vl_
```

## Getting Help

1. **Check logs first**
   ```bash
   docker logs stacks-alloy-agent --tail 100
   journalctl -u alloy -n 100
   ```

2. **Enable debug logging**
   ```alloy
   logging {
     level = "debug"
   }
   ```

3. **Open an issue**
   - Include: version, config (sanitized), error messages
   - https://github.com/alexlmiller/stacks-monitoring/issues
