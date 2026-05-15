import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:lucide_icons/lucide_icons.dart';
import '../../../core/providers/mock_data_provider.dart';
import '../../../core/theme/app_theme.dart';

class CrisisFeedScreen extends ConsumerWidget {
  const CrisisFeedScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final crises = ref.watch(mockCrisisProvider);

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
                      Text(
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
            sliver: SliverList(
              delegate: SliverChildBuilderDelegate((context, index) {
                final crisis = crises[index];
                return ExpandableCrisisCard(crisis: crisis)
                    .animate()
                    .fadeIn(duration: 500.ms, delay: (index * 100).ms)
                    .slideY(begin: 0.1, end: 0);
              }, childCount: crises.length),
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
    final crises = ref.watch(mockCrisisProvider);
    final highSeverityCount = crises.where((c) => c.severity >= 4).length;

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      decoration: BoxDecoration(
        color: AppTheme.cardDark,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.white.withOpacity(0.05)),
      ),
      child: Row(
        children: [
          Icon(LucideIcons.activity, size: 14, color: Colors.green),
          const SizedBox(width: 8),
          Text(
            '${crises.length} ACTIVE',
            style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold),
          ),
          if (highSeverityCount > 0) ...[
            const SizedBox(width: 8),
            Container(width: 1, height: 12, color: Colors.white24),
            const SizedBox(width: 8),
            Icon(
              LucideIcons.alertTriangle,
              size: 14,
              color: AppTheme.crisisRed,
            ),
            const SizedBox(width: 4),
            Text(
              '$highSeverityCount CRITICAL',
              style: TextStyle(
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

class ExpandableCrisisCard extends StatefulWidget {
  final Crisis crisis;
  const ExpandableCrisisCard({super.key, required this.crisis});

  @override
  State<ExpandableCrisisCard> createState() => _ExpandableCrisisCardState();
}

class _ExpandableCrisisCardState extends State<ExpandableCrisisCard> {
  bool _isExpanded = false;

  @override
  Widget build(BuildContext context) {
    return AnimatedContainer(
      duration: const Duration(milliseconds: 300),
      margin: const EdgeInsets.only(bottom: 16),
      decoration: BoxDecoration(
        color: AppTheme.cardDark,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(
          color:
              _isExpanded
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
                  _TypeIcon(type: widget.crisis.type),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          widget.crisis.location,
                          style: Theme.of(context).textTheme.titleLarge,
                        ),
                        Text(
                          '${_formatTime(widget.crisis.timestamp)} • ${_getConfidenceText()}',
                          style: Theme.of(context).textTheme.bodyMedium,
                        ),
                      ],
                    ),
                  ),
                  _SeverityBadge(severity: widget.crisis.severity),
                ],
              ),
              const SizedBox(height: 16),
              Row(
                children: [
                  Expanded(
                    child: _ConfidenceRing(
                      confidence: widget.crisis.confidence,
                    ),
                  ),
                  const SizedBox(width: 16),
                  Expanded(
                    flex: 4,
                    child: Text(
                      widget.crisis.description,
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
                _AgentReasoningSummary(crisis: widget.crisis),
                const SizedBox(height: 16),
                SizedBox(
                  width: double.infinity,
                  child: ElevatedButton(
                    onPressed: () {},
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
    return '${(widget.crisis.confidence * 100).toInt()}% Confidence';
  }

  String _formatTime(DateTime dt) {
    final diff = DateTime.now().difference(dt);
    if (diff.inMinutes < 60) return '${diff.inMinutes}m ago';
    return '${diff.inHours}h ago';
  }
}

class _TypeIcon extends StatelessWidget {
  final CrisisType type;
  const _TypeIcon({required this.type});

  @override
  Widget build(BuildContext context) {
    IconData icon;
    Color color;
    switch (type) {
      case CrisisType.urbanFlooding:
        icon = LucideIcons.waves;
        color = Colors.blue;
        break;
      case CrisisType.heatwave:
        icon = LucideIcons.sun;
        color = Colors.orange;
        break;
      case CrisisType.roadAccident:
        icon = LucideIcons.car;
        color = Colors.red;
        break;
      case CrisisType.fire:
        icon = LucideIcons.flame;
        color = Colors.deepOrange;
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
    Color color =
        confidence > 0.8
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
    Color color =
        severity >= 4
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

class _AgentReasoningSummary extends StatelessWidget {
  final Crisis crisis;
  const _AgentReasoningSummary({required this.crisis});

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Icon(
              LucideIcons.brainCircuit,
              size: 14,
              color: AppTheme.primaryBlue,
            ),
            const SizedBox(width: 8),
            Text(
              'AGENT REASONING',
              style: TextStyle(
                color: AppTheme.primaryBlue,
                fontWeight: FontWeight.bold,
                fontSize: 11,
              ),
            ),
          ],
        ),
        const SizedBox(height: 8),
        Container(
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(
            color: Colors.black26,
            borderRadius: BorderRadius.circular(12),
          ),
          child: Text(
            'Signal fusion detected a cluster of 12 social reports and a 40% water level spike at local sensors. Classification Agent identifies high probability of urban flooding. Cross-referencing with weather API confirms heavy rainfall (45mm/hr).',
            style: TextStyle(
              fontSize: 13,
              color: Colors.white.withOpacity(0.8),
              height: 1.4,
            ),
          ),
        ),
      ],
    );
  }
}
