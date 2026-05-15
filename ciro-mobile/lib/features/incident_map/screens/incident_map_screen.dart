import 'package:flutter/material.dart';
import 'package:google_maps_flutter/google_maps_flutter.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:lucide_icons/lucide_icons.dart';
import '../../../core/providers/mock_data_provider.dart';
import '../../../core/providers/resource_provider.dart';
import '../../../core/theme/app_theme.dart';

class IncidentMapScreen extends ConsumerStatefulWidget {
  const IncidentMapScreen({super.key});

  @override
  ConsumerState<IncidentMapScreen> createState() => _IncidentMapScreenState();
}

class _IncidentMapScreenState extends ConsumerState<IncidentMapScreen> {
  late GoogleMapController mapController;
  final LatLng _center = const LatLng(33.6844, 73.0479);

  void _onMapCreated(GoogleMapController controller) {
    mapController = controller;
  }

  void _showCrisisDetails(Crisis crisis) {
    showModalBottomSheet(
      context: context,
      backgroundColor: AppTheme.backgroundDark,
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(20))),
      builder: (context) => Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                _TypeBadge(type: crisis.type),
                const Spacer(),
                IconButton(icon: const Icon(LucideIcons.x), onPressed: () => Navigator.pop(context)),
              ],
            ),
            const SizedBox(height: 16),
            Text(crisis.location, style: Theme.of(context).textTheme.headlineMedium),
            const SizedBox(height: 8),
            Text(crisis.description, style: Theme.of(context).textTheme.bodyLarge),
            const SizedBox(height: 24),
            Row(
              children: [
                Expanded(
                  child: _StatCard(label: 'SEVERITY', value: 'LVL ${crisis.severity}', color: _getSeverityColor(crisis.severity)),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: _StatCard(label: 'CONFIDENCE', value: '${(crisis.confidence * 100).toInt()}%', color: Colors.green),
                ),
              ],
            ),
            const SizedBox(height: 24),
            SizedBox(
              width: double.infinity,
              height: 50,
              child: ElevatedButton(
                onPressed: () {},
                style: ElevatedButton.styleFrom(backgroundColor: AppTheme.primaryBlue, foregroundColor: Colors.white),
                child: const Text('VIEW FULL INCIDENT LOGS'),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Color _getSeverityColor(int severity) {
    if (severity >= 4) return AppTheme.crisisRed;
    if (severity >= 3) return AppTheme.emergencyOrange;
    return Colors.yellow;
  }

  @override
  Widget build(BuildContext context) {
    final crises = ref.watch(mockCrisisProvider);
    final resources = ref.watch(mockResourceProvider);

    Set<Marker> markers = {};
    Set<Circle> circles = {};
    Set<Polyline> polylines = {};

    // Crisis Markers & Circles
    for (var crisis in crises) {
      markers.add(
        Marker(
          markerId: MarkerId(crisis.id),
          position: LatLng(crisis.lat, crisis.lng),
          onTap: () => _showCrisisDetails(crisis),
          icon: BitmapDescriptor.defaultMarkerWithHue(_getHueForType(crisis.type)),
        ),
      );

      circles.add(
        Circle(
          circleId: CircleId('circle_${crisis.id}'),
          center: LatLng(crisis.lat, crisis.lng),
          radius: 500 + (crisis.severity * 200).toDouble(),
          fillColor: _getSeverityColor(crisis.severity).withOpacity(0.15),
          strokeColor: _getSeverityColor(crisis.severity),
          strokeWidth: 2,
        ),
      );
    }

    // Resource Markers & Routes
    for (var resource in resources) {
      markers.add(
        Marker(
          markerId: MarkerId(resource.id),
          position: resource.location,
          icon: BitmapDescriptor.defaultMarkerWithHue(BitmapDescriptor.hueAzure),
          infoWindow: InfoWindow(title: '${resource.type.name.toUpperCase()} - ${resource.status}'),
        ),
      );

      if (resource.assignedIncidentId != null) {
        final assignedCrisis = crises.firstWhere((c) => c.id == resource.assignedIncidentId);
        polylines.add(
          Polyline(
            polylineId: PolylineId('route_${resource.id}_${assignedCrisis.id}'),
            points: [resource.location, LatLng(assignedCrisis.lat, assignedCrisis.lng)],
            color: AppTheme.primaryBlue.withOpacity(0.6),
            width: 3,
            patterns: [PatternItem.dash(20), PatternItem.gap(10)],
          ),
        );
      }
    }

    return Scaffold(
      body: GoogleMap(
        onMapCreated: _onMapCreated,
        initialCameraPosition: CameraPosition(target: _center, zoom: 13.0),
        markers: markers,
        circles: circles,
        polylines: polylines,
        style: _mapStyle,
        myLocationEnabled: false,
        myLocationButtonEnabled: false,
        zoomControlsEnabled: false,
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () => mapController.animateCamera(CameraUpdate.newLatLng(_center)),
        backgroundColor: AppTheme.cardDark,
        child: const Icon(LucideIcons.compass),
      ),
    );
  }

  double _getHueForType(CrisisType type) {
    switch (type) {
      case CrisisType.urbanFlooding: return BitmapDescriptor.hueBlue;
      case CrisisType.heatwave: return BitmapDescriptor.hueOrange;
      case CrisisType.roadAccident: return BitmapDescriptor.hueRed;
      case CrisisType.fire: return BitmapDescriptor.hueRed;
      default: return BitmapDescriptor.hueYellow;
    }
  }

  final String _mapStyle = '''
[
  {
    "elementType": "geometry",
    "stylers": [{"color": "#212121"}]
  },
  {
    "elementType": "labels.icon",
    "stylers": [{"visibility": "off"}]
  },
  {
    "elementType": "labels.text.fill",
    "stylers": [{"color": "#757575"}]
  },
  {
    "elementType": "labels.text.stroke",
    "stylers": [{"color": "#212121"}]
  },
  {
    "featureType": "administrative",
    "elementType": "geometry",
    "stylers": [{"color": "#757575"}]
  },
  {
    "featureType": "water",
    "elementType": "geometry",
    "stylers": [{"color": "#000000"}]
  }
]
''';
}

class _TypeBadge extends StatelessWidget {
  final CrisisType type;
  const _TypeBadge({required this.type});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      decoration: BoxDecoration(
        color: AppTheme.primaryBlue.withOpacity(0.1),
        borderRadius: BorderRadius.circular(20),
      ),
      child: Text(type.name.toUpperCase(), style: TextStyle(color: AppTheme.primaryBlue, fontWeight: FontWeight.bold, fontSize: 12)),
    );
  }
}

class _StatCard extends StatelessWidget {
  final String label;
  final String value;
  final Color color;
  const _StatCard({required this.label, required this.value, required this.color});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.black26,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.white.withOpacity(0.05)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(label, style: const TextStyle(fontSize: 10, color: Colors.white54, fontWeight: FontWeight.bold)),
          const SizedBox(height: 4),
          Text(value, style: TextStyle(fontSize: 18, color: color, fontWeight: FontWeight.bold)),
        ],
      ),
    );
  }
}
