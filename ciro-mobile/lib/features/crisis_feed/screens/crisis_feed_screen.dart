import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:lucide_icons/lucide_icons.dart';
import '../../../core/providers/incident_provider.dart';
import '../../../core/theme/app_theme.dart';
import '../../../data/models/incident.dart';
import 'incident_detail_screen.dart';

class CrisisFeedScreen extends ConsumerWidget {
  const CrisisFeedScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final incidents = ref.watch(incidentProvider);

    return Scaffold(
      body: CustomScrollView(
        slivers: [
          SliverAppBar(
            expandedHeight: 120,
            floating: true,
            backgroundColor: AppTheme.backgroundDark,
            flexibleSpace: FlexibleSpaceBar(
              background: SafeArea(
                child: Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    mainAxisAlignment: MainAxisAlignment.end,
                    children: [
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Expanded(
                            child: Text(
                              'CIRO',
                              style: Theme.of(context).textTheme.headlineMedium,
                              overflow: TextOverflow.ellipsis,
                            ),
                          ),
                          const SizedBox(width: 12),
                          const CityStatusBar(),
                        ],
                      ),
                      const SizedBox(height: 8),
                      const Text(
                        'CITY MONITORING ACTIVE',
                        style: TextStyle(
                          color: Colors.green,
                          fontSize: 10,
                          fontWeight: FontWeight.bold,
                          letterSpacing: 1.2,
                        ),
                      ),
                      const SizedBox(height: 16),
                    ],
                  ),
                ),
              ),
            ),
          ),
          SliverPadding(
            padding: const EdgeInsets.all(16),
            sliver: incidents.isEmpty
                ? const SliverFillRemaining(
                    child: Center(
                      child: Text(
                        'No active incidents detected.\nTrigger a demo scenario in the backend.',
                        textAlign: TextAlign.center,
                        style: TextStyle(color: Colors.white24),
                      ),
                    ),
                  )
                : SliverList(
                    delegate: SliverChildBuilderDelegate((context, index) {
                      final incident = incidents[index];
                      return IncidentCard(incident: incident)
                          .animate()
                          .fadeIn(duration: 500.ms, delay: (index * 100).ms)
                          .slideY(begin: 0.1, end: 0);
                    }, childCount: incidents.length),
                  ),
          ),
        ],
      ),
    );
  }
}

class CityStatusBar extends ConsumerWidget {
  const CityStatusBar({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final incidents = ref.watch(incidentProvider);
    final highSeverityCount = incidents.where((i) => (i.classification?.severity ?? 0) >= 4).length;

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      decoration: BoxDecoration(
        color: AppTheme.cardDark,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.white.withOpacity(0.05)),
      ),
      child: Row(
        children: [
          const Icon(LucideIcons.activity, size: 14, color: Colors.green),
          const SizedBox(width: 8),
          Text(
            '${incidents.length} ACTIVE',
            style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold),
          ),
          if (highSeverityCount > 0) ...[
            const SizedBox(width: 8),
            Container(width: 1, height: 12, color: Colors.white24),
            const SizedBox(width: 8),
            const Icon(
              LucideIcons.alertTriangle,
              size: 14,
              color: AppTheme.crisisRed,
            ),
            const SizedBox(width: 4),
            Text(
              '$highSeverityCount CRITICAL',
              style: const TextStyle(
                color: AppTheme.crisisRed,
                fontSize: 12,
                fontWeight: FontWeight.bold,
              ),
            ),
          ],
        ],
      ),
    );
  }
}

class IncidentCard extends StatefulWidget {
  final Incident incident;
  const IncidentCard({super.key, required this.incident});

  @override
  State<IncidentCard> createState() => _IncidentCardState();
}

class _IncidentCardState extends State<IncidentCard> {
  bool _isExpanded = false;

  @override
  Widget build(BuildContext context) {
    final cls = widget.incident.classification;
    
    return AnimatedContainer(
      duration: const Duration(milliseconds: 300),
      margin: const EdgeInsets.only(bottom: 16),
      decoration: BoxDecoration(
        color: AppTheme.cardDark,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(
          color: _isExpanded
              ? AppTheme.primaryBlue.withOpacity(0.5)
              : Colors.white.withOpacity(0.05),
          width: 1,
        ),
      ),
      child: InkWell(
        onTap: () => setState(() => _isExpanded = !_isExpanded),
        borderRadius: BorderRadius.circular(20),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  _TypeIcon(type: cls?.crisisType ?? 'unknown'),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          widget.incident.location.areaName,
                          style: Theme.of(context).textTheme.titleLarge,
                        ),
                        Text(
                          '${_formatTime(widget.incident.updatedAt)} • ${_getConfidenceText()}',
                          style: Theme.of(context).textTheme.bodyMedium,
                        ),
                      ],
                    ),
                  ),
                  if (cls != null) _SeverityBadge(severity: cls.severity),
                ],
              ),
              const SizedBox(height: 16),
              Row(
                children: [
                  Expanded(
                    child: _ConfidenceRing(
                      confidence: cls?.confidence ?? 0.0,
                    ),
                  ),
                  const SizedBox(width: 16),
                  Expanded(
                    flex: 4,
                    child: Text(
                      cls?.reasoning ?? 'Initial signal fusion in progress. Agents are classifying the event...',
                      style: Theme.of(context).textTheme.bodyLarge,
                      maxLines: _isExpanded ? 10 : 2,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                ],
              ),
              if (_isExpanded) ...[
                const SizedBox(height: 24),
                const Divider(height: 1, color: Colors.white10),
                const SizedBox(height: 16),
                _AgentPipelineStatus(stage: widget.incident.pipelineStage),
                const SizedBox(height: 16),
                SizedBox(
                  width: double.infinity,
                  child: ElevatedButton(
                    onPressed: () {
                      Navigator.push(
                        context,
                        MaterialPageRoute(
                          builder: (context) => IncidentDetailScreen(
                            incident: widget.incident,
                          ),
                        ),
                      );
                    },
                    style: ElevatedButton.styleFrom(
                      backgroundColor: AppTheme.primaryBlue,
                      foregroundColor: Colors.white,
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(12),
                      ),
                    ),
                    child: const Text('VIEW FULL INTELLIGENCE'),
                  ),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }

  String _getConfidenceText() {
    final confidence = widget.incident.classification?.confidence ?? 0.0;
    return '${(confidence * 100).toInt()}% Confidence';
  }

  String _formatTime(DateTime dt) {
    final diff = DateTime.now().difference(dt);
    if (diff.inMinutes < 60) return '${diff.inMinutes}m ago';
    return '${diff.inHours}h ago';
  }
}

class _TypeIcon extends StatelessWidget {
  final String type;
  const _TypeIcon({required this.type});

  @override
  Widget build(BuildContext context) {
    IconData icon;
    Color color;
    switch (type.toLowerCase()) {
      case 'urban_flooding':
        icon = LucideIcons.waves;
        color = Colors.blue;
        break;
      case 'heatwave':
        icon = LucideIcons.sun;
        color = Colors.orange;
        break;
      case 'fire':
        icon = LucideIcons.flame;
        color = Colors.deepOrange;
        break;
      case 'infrastructure_failure':
        icon = LucideIcons.building;
        color = Colors.grey;
        break;
      default:
        icon = LucideIcons.alertTriangle;
        color = Colors.yellow;
    }

    return Container(
      padding: const EdgeInsets.all(10),
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        shape: BoxShape.circle,
      ),
      child: Icon(icon, size: 20, color: color),
    );
  }
}

class _ConfidenceRing extends StatelessWidget {
  final double confidence;
  const _ConfidenceRing({required this.confidence});

  @override
  Widget build(BuildContext context) {
    Color color = confidence > 0.8
        ? Colors.green
        : (confidence > 0.5 ? Colors.orange : Colors.red);
    return SizedBox(
      height: 60,
      width: 60,
      child: Stack(
        alignment: Alignment.center,
        children: [
          CircularProgressIndicator(
            value: confidence,
            backgroundColor: Colors.white.withOpacity(0.05),
            color: color,
            strokeWidth: 6,
          ),
          Text(
            '${(confidence * 100).toInt()}%',
            style: TextStyle(
              fontWeight: FontWeight.bold,
              fontSize: 12,
              color: color,
            ),
          ),
        ],
      ),
    );
  }
}

class _SeverityBadge extends StatelessWidget {
  final int severity;
  const _SeverityBadge({required this.severity});

  @override
  Widget build(BuildContext context) {
    Color color = severity >= 4
        ? AppTheme.crisisRed
        : (severity >= 3 ? AppTheme.emergencyOrange : Colors.yellow);
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: color.withOpacity(0.3)),
      ),
      child: Text(
        'LVL $severity',
        style: TextStyle(
          color: color,
          fontSize: 10,
          fontWeight: FontWeight.bold,
        ),
      ),
    );
  }
}

class _AgentPipelineStatus extends StatelessWidget {
  final String stage;
  const _AgentPipelineStatus({required this.stage});

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            const Icon(
              LucideIcons.brainCircuit,
              size: 14,
              color: AppTheme.primaryBlue,
            ),
            const SizedBox(width: 8),
            Text(
              'PIPELINE STAGE: ${stage.toUpperCase()}',
              style: const TextStyle(
                color: AppTheme.primaryBlue,
                fontWeight: FontWeight.bold,
                fontSize: 11,
              ),
            ),
          ],
        ),
      ],
    );
  }
}
