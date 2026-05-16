class AgentTrace {
  final String traceId;
  final String incidentId;
  final String agent;
  final DateTime timestamp;
  final String inputSummary;
  final String reasoning;
  final Map<String, dynamic> output;
  final String decision;
  final String? nextAgent;
  final int latencyMs;
  final String? model;
  final bool isDegraded;

  AgentTrace({
    required this.traceId,
    required this.incidentId,
    required this.agent,
    required this.timestamp,
    required this.inputSummary,
    required this.reasoning,
    required this.output,
    required this.decision,
    this.nextAgent,
    this.latencyMs = 0,
    this.model,
    this.isDegraded = false,
  });

  factory AgentTrace.fromJson(Map<String, dynamic> json) {
    return AgentTrace(
      traceId: json['trace_id'] as String,
      incidentId: json['incident_id'] as String,
      agent: json['agent'] as String,
      timestamp: DateTime.parse(json['timestamp'] as String),
      inputSummary: json['input_summary'] as String,
      reasoning: json['reasoning'] as String,
      output: Map<String, dynamic>.from(json['output'] ?? {}),
      decision: json['decision'] as String,
      nextAgent: json['next_agent'] as String?,
      latencyMs: json['latency_ms'] as int? ?? 0,
      model: json['model'] as String?,
      isDegraded: json['is_degraded'] as bool? ?? false,
    );
  }

  Map<String, dynamic> toJson() => {
    'trace_id': traceId,
    'incident_id': incidentId,
    'agent': agent,
    'timestamp': timestamp.toIso8601String(),
    'input_summary': inputSummary,
    'reasoning': reasoning,
    'output': output,
    'decision': decision,
    'next_agent': nextAgent,
    'latency_ms': latencyMs,
    'model': model,
    'is_degraded': isDegraded,
  };
}
