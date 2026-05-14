import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:google_maps_flutter/google_maps_flutter.dart';

enum ResourceType {
  ambulance,
  police,
  fireTruck,
  rescueTeam,
}

class EmergencyResource {
  final String id;
  final ResourceType type;
  final LatLng location;
  final String status; // "Available", "Deployed", "En Route"
  final String? assignedIncidentId;

  EmergencyResource({
    required this.id,
    required this.type,
    required this.location,
    required this.status,
    this.assignedIncidentId,
  });
}

final mockResourceProvider = Provider<List<EmergencyResource>>((ref) {
  return [
    EmergencyResource(
      id: 'amb_01',
      type: ResourceType.ambulance,
      location: const LatLng(33.685, 73.050),
      status: 'En Route',
      assignedIncidentId: 'inc_g10_flood_001',
    ),
    EmergencyResource(
      id: 'pol_02',
      type: ResourceType.police,
      location: const LatLng(33.675, 73.040),
      status: 'Available',
    ),
    EmergencyResource(
      id: 'res_03',
      type: ResourceType.rescueTeam,
      location: const LatLng(33.680, 73.060),
      status: 'Deployed',
      assignedIncidentId: 'inc_h3_heat_002',
    ),
  ];
});
