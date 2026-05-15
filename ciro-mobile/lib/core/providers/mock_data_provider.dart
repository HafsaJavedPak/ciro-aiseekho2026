import 'package:flutter_riverpod/flutter_riverpod.dart';

enum CrisisType {
  urbanFlooding,
  heatwave,
  roadAccident,
  powerOutage,
  fire,
  infrastructureFailure,
}

extension CrisisTypeExtension on CrisisType {
  String get displayName {
    switch (this) {
      case CrisisType.urbanFlooding: return 'Urban Flooding';
      case CrisisType.heatwave: return 'Heatwave';
      case CrisisType.roadAccident: return 'Road Accident';
      case CrisisType.powerOutage: return 'Power Outage';
      case CrisisType.fire: return 'Fire';
      case CrisisType.infrastructureFailure: return 'Infrastructure Failure';
    }
  }
}

class Crisis {
  final String id;
  final CrisisType type;
  final int severity; // 1-5
  final double confidence; // 0.0-1.0
  final String location;
  final double lat;
  final double lng;
  final DateTime timestamp;
  final String description;

  Crisis({
    required this.id,
    required this.type,
    required this.severity,
    required this.confidence,
    required this.location,
    required this.lat,
    required this.lng,
    required this.timestamp,
    required this.description,
  });
}

final mockCrisisProvider = Provider<List<Crisis>>((ref) {
  return [
    Crisis(
      id: 'inc_g10_flood_001',
      type: CrisisType.urbanFlooding,
      severity: 4,
      confidence: 0.78,
      location: 'G-10, Islamabad',
      lat: 33.681,
      lng: 73.048,
      timestamp: DateTime.now().subtract(const Duration(minutes: 12)),
      description: 'Multiple high-confidence signals co-located in G-10 sector. Dominant hypothesis: urban flooding.',
    ),
    Crisis(
      id: 'inc_h3_heat_002',
      type: CrisisType.heatwave,
      severity: 3,
      confidence: 0.92,
      location: 'H-3, Islamabad',
      lat: 33.690,
      lng: 73.060,
      timestamp: DateTime.now().subtract(const Duration(hours: 1)),
      description: 'Temperatures exceeding 45°C. High risk for vulnerable populations.',
    ),
  ];
});
