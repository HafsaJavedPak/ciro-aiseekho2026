import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:lucide_icons/lucide_icons.dart';
import 'package:flutter_animate/flutter_animate.dart';
import '../../../core/theme/app_theme.dart';

class AlertsScreen extends ConsumerStatefulWidget {
  const AlertsScreen({super.key});

  @override
  ConsumerState<AlertsScreen> createState() => _AlertsScreenState();
}

class _AlertsScreenState extends ConsumerState<AlertsScreen> with SingleTickerProviderStateMixin {
  late TabController _tabController;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 4, vsync: this);
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('STAKEHOLDER ALERTS'),
        bottom: TabBar(
          controller: _tabController,
          isScrollable: true,
          indicatorColor: AppTheme.primaryBlue,
          labelColor: AppTheme.primaryBlue,
          unselectedLabelColor: Colors.white38,
          tabs: const [
            Tab(text: 'PUBLIC', icon: Icon(LucideIcons.users, size: 18)),
            Tab(text: 'EMERGENCY', icon: Icon(LucideIcons.siren, size: 18)),
            Tab(text: 'HOSPITAL', icon: Icon(LucideIcons.activity, size: 18)),
            Tab(text: 'UTILITY', icon: Icon(LucideIcons.zap, size: 18)),
          ],
        ),
      ),
      body: TabBarView(
        controller: _tabController,
        children: [
          _AlertList(type: 'public'),
          _AlertList(type: 'emergency'),
          _AlertList(type: 'hospital'),
          _AlertList(type: 'utility'),
        ],
      ),
    );
  }
}

class _AlertList extends StatelessWidget {
  final String type;
  const _AlertList({required this.type});

  @override
  Widget build(BuildContext context) {
    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: 2,
      itemBuilder: (context, index) {
        return _AlertCard(index: index, type: type)
            .animate()
            .fadeIn(delay: (index * 200).ms)
            .slideY(begin: 0.1, end: 0);
      },
    );
  }
}

class _AlertCard extends StatelessWidget {
  final int index;
  final String type;
  const _AlertCard({required this.index, required this.type});

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppTheme.cardDark,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.white.withOpacity(0.05)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: Colors.red.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(4),
                ),
                child: const Text(
                  'HIGH URGENCY',
                  style: TextStyle(color: Colors.red, fontSize: 10, fontWeight: FontWeight.bold),
                ),
              ),
              const Text('12m ago', style: TextStyle(fontSize: 10, color: Colors.white24)),
            ],
          ),
          const SizedBox(height: 12),
          const Text(
            'URBAN FLOODING ALERT - G-10 SECTOR',
            style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
          ),
          const SizedBox(height: 8),
          Text(
            _getSampleMessage(type),
            style: TextStyle(fontSize: 14, color: Colors.white.withOpacity(0.7), height: 1.5),
          ),
          const SizedBox(height: 16),
          Row(
            children: [
              const Icon(LucideIcons.checkCircle, size: 14, color: Colors.green),
              const SizedBox(width: 6),
              const Text('Broadcast successful', style: TextStyle(color: Colors.green, fontSize: 11)),
              const Spacer(),
              TextButton.icon(
                onPressed: () {},
                icon: const Icon(LucideIcons.copy, size: 14),
                label: const Text('COPY', style: TextStyle(fontSize: 11)),
                style: TextButton.styleFrom(foregroundColor: AppTheme.primaryBlue),
              ),
            ],
          ),
        ],
      ),
    );
  }

  String _getSampleMessage(String type) {
    switch (type) {
      case 'public':
        return 'URGENT: Flash flooding in G-10. Avoid George Town area. Reroute via 9th Avenue. Emergency services on site.';
      case 'emergency':
        return 'CRITICAL: Deploy Rescue Team Alpha to G-10/3. Water depth 1.8m. 12 vehicles stranded. Coordination channel 7.';
      case 'hospital':
        return 'NOTIFICATION: Expect influx of 5-10 trauma cases from G-10 sector. Prep triage area 2. ETA 15 mins.';
      case 'utility':
        return 'ALERT: Grid sub-station G-10 at risk of inundation. Power cut advised for blocks 1-4 to prevent infrastructure failure.';
      default:
        return '';
    }
  }
}
