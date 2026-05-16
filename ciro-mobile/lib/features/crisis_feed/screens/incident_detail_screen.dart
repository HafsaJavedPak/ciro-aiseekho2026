import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:lucide_icons/lucide_icons.dart';
import 'package:intl/intl.dart';
import '../../../data/models/incident.dart';
import '../../../core/theme/app_theme.dart';
import '../../traces/screens/agent_traces_screen.dart';

class IncidentDetailScreen extends ConsumerWidget {
  final Incident incident;
  const IncidentDetailScreen({super.key, required this.incident});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('CRISIS INTELLIGENCE'),
        actions: [
          IconButton(
            icon: const Icon(LucideIcons.share2),
            onPressed: () {},
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _buildHeader(context),
            const SizedBox(height: 24),
            _buildClassificationCard(context),
            const SizedBox(height: 24),
            _buildSectionHeader(context, 'CONTRIBUTING SIGNALS', LucideIcons.rss),
            const SizedBox(height: 12),
            _buildSignalsList(context),
            const SizedBox(height: 32),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton.icon(
                onPressed: () {
                  Navigator.push(
                    context,
                    MaterialPageRoute(
                      builder: (context) => AgentTracesScreen(incidentId: incident.incidentId),
                    ),
                  );
                },
                icon: const Icon(LucideIcons.activity),
                label: const Text('VIEW AGENT REASONING TRACES'),
                style: ElevatedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(vertical: 16),
                  backgroundColor: AppTheme.primaryBlue,
                  foregroundColor: Colors.white,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildHeader(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  incident.location.areaName,
                  style: Theme.of(context).textTheme.headlineMedium,
                ),
                Text(
                  'ID: ${incident.incidentId} • ${DateFormat('HH:mm').format(incident.createdAt)}',
                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(color: Colors.white54),
                ),
              ],
            ),
            _StatusBadge(status: incident.status),
          ],
        ),
      ],
    );
  }

  Widget _buildClassificationCard(BuildContext context) {
    final cls = incident.classification;
    if (cls == null) return const SizedBox.shrink();

    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: AppTheme.cardDark,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: Colors.white.withOpacity(0.05)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              _ConfidenceRing(confidence: cls.confidence),
              const SizedBox(width: 20),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      cls.crisisType.toUpperCase().replaceAll('_', ' '),
                      style: Theme.of(context).textTheme.titleLarge?.copyWith(
                        color: AppTheme.primaryBlue,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 4),
                    _SeverityIndicator(severity: cls.severity),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 20),
          const Divider(color: Colors.white10),
          const SizedBox(height: 16),
          Text(
            'REASONING',
            style: TextStyle(
              color: Colors.white.withOpacity(0.4),
              fontSize: 10,
              fontWeight: FontWeight.bold,
              letterSpacing: 1.2,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            cls.reasoning,
            style: Theme.of(context).textTheme.bodyLarge?.copyWith(height: 1.5),
          ),
          if (cls.counterHypothesis != null) ...[
            const SizedBox(height: 16),
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.black26,
                borderRadius: BorderRadius.circular(12),
              ),
              child: Row(
                children: [
                  const Icon(LucideIcons.helpCircle, size: 16, color: Colors.orange),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Text(
                      'Counter-Hypothesis: ${cls.counterHypothesis} (${(cls.counterConfidence! * 100).toInt()}%)',
                      style: const TextStyle(fontSize: 12, color: Colors.orange),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildSectionHeader(BuildContext context, String title, IconData icon) {
    return Row(
      children: [
        Icon(icon, size: 16, color: AppTheme.primaryBlue),
        const SizedBox(width: 8),
        Text(
          title,
          style: const TextStyle(
            fontWeight: FontWeight.bold,
            letterSpacing: 1.2,
            fontSize: 12,
            color: Colors.white70,
          ),
        ),
      ],
    );
  }

  Widget _buildSignalsList(BuildContext context) {
    // In a real app, we would fetch signals from the provider
    // For now, we'll show a placeholder list
    return Column(
      children: List.generate(3, (index) => _SignalItem(index: index)),
    );
  }
}

class _StatusBadge extends StatelessWidget {
  final String status;
  const _StatusBadge({required this.status});

  @override
  Widget build(BuildContext context) {
    Color color = status == 'active' ? Colors.green : Colors.orange;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: color.withOpacity(0.3)),
      ),
      child: Text(
        status.toUpperCase(),
        style: TextStyle(color: color, fontSize: 10, fontWeight: FontWeight.bold),
      ),
    );
  }
}

class _ConfidenceRing extends StatelessWidget {
  final double confidence;
  const _ConfidenceRing({required this.confidence});

  @override
  Widget build(BuildContext context) {
    Color color = confidence > 0.8 ? Colors.green : (confidence > 0.5 ? Colors.orange : Colors.red);
    return SizedBox(
      height: 70,
      width: 70,
      child: Stack(
        alignment: Alignment.center,
        children: [
          CircularProgressIndicator(
            value: confidence,
            backgroundColor: Colors.white.withOpacity(0.05),
            color: color,
            strokeWidth: 8,
          ),
          Text(
            '${(confidence * 100).toInt()}%',
            style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16, color: color),
          ),
        ],
      ),
    );
  }
}

class _SeverityIndicator extends StatelessWidget {
  final int severity;
  const _SeverityIndicator({required this.severity});

  @override
  Widget build(BuildContext context) {
    return Row(
      children: List.generate(5, (index) {
        return Container(
          width: 20,
          height: 6,
          margin: const EdgeInsets.only(right: 4),
          decoration: BoxDecoration(
            color: index < severity ? AppTheme.crisisRed : Colors.white10,
            borderRadius: BorderRadius.circular(2),
          ),
        );
      }),
    );
  }
}

class _SignalItem extends StatelessWidget {
  final int index;
  const _SignalItem({required this.index});

  @override
  Widget build(BuildContext context) {
    final types = ['weather', 'social', 'sensor'];
    final type = types[index % 3];
    
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: AppTheme.cardDark.withOpacity(0.5),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Row(
        children: [
          _getIconForType(type),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  _getTitleForType(type),
                  style: const TextStyle(fontWeight: FontWeight.bold),
                ),
                Text(
                  _getContentForType(type),
                  style: const TextStyle(fontSize: 12, color: Colors.white54),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
              ],
            ),
          ),
          const Text('2m ago', style: TextStyle(fontSize: 10, color: Colors.white24)),
        ],
      ),
    );
  }

  Widget _getIconForType(String type) {
    IconData icon;
    Color color;
    switch (type) {
      case 'weather': icon = LucideIcons.cloudRain; color = Colors.blue; break;
      case 'social': icon = LucideIcons.twitter; color = Colors.lightBlue; break;
      case 'sensor': icon = LucideIcons.cpu; color = Colors.purple; break;
      default: icon = LucideIcons.rss; color = Colors.grey;
    }
    return Icon(icon, size: 20, color: color);
  }

  String _getTitleForType(String type) => type.toUpperCase();
  String _getContentForType(String type) {
    switch (type) {
      case 'weather': return 'Heavy rainfall alert: 45mm/hr';
      case 'social': return 'Street flooded at G-10/3 Markaz';
      case 'sensor': return 'Water level breach: 1.8m';
      default: return '';
    }
  }
}
