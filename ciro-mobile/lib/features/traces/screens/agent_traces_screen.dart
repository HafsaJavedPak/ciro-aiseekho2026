import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:lucide_icons/lucide_icons.dart';
import 'package:intl/intl.dart';
import 'package:flutter_animate/flutter_animate.dart';
import '../../../data/models/trace.dart';
import '../../../core/theme/app_theme.dart';

class AgentTracesScreen extends ConsumerWidget {
  final String incidentId;
  const AgentTracesScreen({super.key, required this.incidentId});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    // In a real app, this would be a StreamBuilder or ref.watch(tracesProvider(incidentId))
    final mockTraces = _getMockTraces();

    return Scaffold(
      appBar: AppBar(
        title: const Text('AGENT REASONING TRACES'),
      ),
      body: Column(
        children: [
          _buildIncidentBanner(context),
          Expanded(
            child: ListView.builder(
              padding: const EdgeInsets.all(16),
              itemCount: mockTraces.length,
              itemBuilder: (context, index) {
                return _TraceItem(
                  trace: mockTraces[index],
                  isFirst: index == 0,
                  isLast: index == mockTraces.length - 1,
                ).animate().fadeIn(delay: (index * 150).ms).slideX(begin: 0.05, end: 0);
              },
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildIncidentBanner(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      color: AppTheme.primaryBlue.withOpacity(0.1),
      child: Row(
        children: [
          const Icon(LucideIcons.info, size: 16, color: AppTheme.primaryBlue),
          const SizedBox(width: 12),
          Text(
            'Tracing Incident: $incidentId',
            style: const TextStyle(
              color: AppTheme.primaryBlue,
              fontWeight: FontWeight.bold,
              fontSize: 12,
            ),
          ),
          const Spacer(),
          const Icon(LucideIcons.wifi, size: 14, color: Colors.green),
          const SizedBox(width: 4),
          const Text('LIVE', style: TextStyle(color: Colors.green, fontSize: 10, fontWeight: FontWeight.bold)),
        ],
      ),
    );
  }

  List<AgentTrace> _getMockTraces() {
    return [
      AgentTrace(
        traceId: 'tr_1',
        incidentId: incidentId,
        agent: 'Signal Fusion Agent',
        timestamp: DateTime.now().subtract(const Duration(minutes: 10)),
        inputSummary: '12 social posts, 1 weather alert, 2 sensor readings',
        reasoning: 'Spatiotemporal clustering identified high signal density in G-10 sector. Co-occurrence of water level spike (+40%) and heavy rain reports (conf=0.88) suggests a single coherent event.',
        output: {'status': 'fused', 'confidence': 0.85},
        decision: 'FUSE_AND_PROCEED',
        nextAgent: 'Classification Agent',
        latencyMs: 450,
        model: 'Gemini 1.5 Flash',
      ),
      AgentTrace(
        traceId: 'tr_2',
        incidentId: incidentId,
        agent: 'Classification Agent',
        timestamp: DateTime.now().subtract(const Duration(minutes: 9)),
        inputSummary: 'Fused incident context (lat: 33.68, lng: 73.05)',
        reasoning: 'Based on signal types (flood, rain, stalled vehicles) and sensor data (1.8m depth), this is classified as Urban Flooding. Confidence is high due to multi-source agreement.',
        output: {'type': 'urban_flooding', 'severity': 4, 'confidence': 0.78},
        decision: 'CLASSIFY_AS_CRISIS',
        nextAgent: 'Resource Allocation Agent',
        latencyMs: 1200,
        model: 'Gemini 1.5 Pro',
      ),
      AgentTrace(
        traceId: 'tr_3',
        incidentId: incidentId,
        agent: 'Resource Allocation Agent',
        timestamp: DateTime.now().subtract(const Duration(minutes: 8)),
        inputSummary: 'Crisis: Urban Flooding, Severity: 4',
        reasoning: 'Prioritizing G-10 flooding due to high population density (8,400 affected). Assigning 3 ambulances and 1 rescue team. Deficit detected for secondary incident in I-9; redirecting police unit as backup.',
        output: {'assigned': ['AMB_1', 'AMB_2', 'AMB_3', 'RESCUE_A'], 'conflicts': 1},
        decision: 'ALLOCATE_RESOURCES',
        nextAgent: 'Stakeholder Messaging Agent',
        latencyMs: 850,
        model: 'Gemini 1.5 Flash',
      ),
    ];
  }
}

class _TraceItem extends StatefulWidget {
  final AgentTrace trace;
  final bool isFirst;
  final bool isLast;
  const _TraceItem({required this.trace, required this.isFirst, required this.isLast});

  @override
  State<_TraceItem> createState() => _TraceItemState();
}

class _TraceItemState extends State<_TraceItem> {
  bool _isExpanded = false;

  @override
  Widget build(BuildContext context) {
    return IntrinsicHeight(
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _buildTimelinePart(),
          const SizedBox(width: 16),
          Expanded(
            child: _buildTraceCard(),
          ),
        ],
      ),
    );
  }

  Widget _buildTimelinePart() {
    return SizedBox(
      width: 20,
      child: Column(
        children: [
          Container(
            width: 2,
            height: 10,
            color: widget.isFirst ? Colors.transparent : Colors.white10,
          ),
          Container(
            width: 12,
            height: 12,
            decoration: BoxDecoration(
              color: AppTheme.primaryBlue,
              shape: BoxShape.circle,
              boxShadow: [
                BoxShadow(color: AppTheme.primaryBlue.withOpacity(0.5), blurRadius: 8, spreadRadius: 2),
              ],
            ),
          ),
          Expanded(
            child: Container(
              width: 2,
              color: widget.isLast ? Colors.transparent : Colors.white10,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildTraceCard() {
    return GestureDetector(
      onTap: () => setState(() => _isExpanded = !_isExpanded),
      child: Container(
        margin: const EdgeInsets.only(bottom: 24),
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: AppTheme.cardDark,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(
            color: _isExpanded ? AppTheme.primaryBlue.withOpacity(0.3) : Colors.white.withOpacity(0.05),
          ),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  widget.trace.agent.toUpperCase(),
                  style: TextStyle(
                    color: AppTheme.primaryBlue,
                    fontWeight: FontWeight.bold,
                    fontSize: 11,
                    letterSpacing: 1.1,
                  ),
                ),
                Text(
                  DateFormat('HH:mm:ss').format(widget.trace.timestamp),
                  style: const TextStyle(fontSize: 10, color: Colors.white24),
                ),
              ],
            ),
            const SizedBox(height: 8),
            Text(
              widget.trace.decision.replaceAll('_', ' '),
              style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15),
            ),
            const SizedBox(height: 8),
            Text(
              widget.trace.reasoning,
              style: TextStyle(fontSize: 13, color: Colors.white.withOpacity(0.7), height: 1.4),
              maxLines: _isExpanded ? 20 : 2,
              overflow: TextOverflow.ellipsis,
            ),
            if (_isExpanded) ...[
              const SizedBox(height: 16),
              const Divider(color: Colors.white10),
              const SizedBox(height: 12),
              _buildDetailRow('Input Summary', widget.trace.inputSummary),
              _buildDetailRow('Model', widget.trace.model ?? 'N/A'),
              _buildDetailRow('Latency', '${widget.trace.latencyMs}ms'),
              _buildDetailRow('Next Agent', widget.trace.nextAgent ?? 'NONE'),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildDetailRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 6),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 100,
            child: Text(
              label,
              style: const TextStyle(fontSize: 11, color: Colors.white38, fontWeight: FontWeight.bold),
            ),
          ),
          Expanded(
            child: Text(
              value,
              style: const TextStyle(fontSize: 11, color: Colors.white70),
            ),
          ),
        ],
      ),
    );
  }
}
