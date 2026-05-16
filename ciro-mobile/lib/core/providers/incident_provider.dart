import 'dart:async';
import 'dart:convert';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../data/models/incident.dart';
import '../api/api_client.dart';
import '../websocket/ws_client.dart';

class IncidentNotifier extends StateNotifier<List<Incident>> {
  IncidentNotifier() : super([]) {
    _initialize();
  }

  void _initialize() async {
    wsClient.connect();
    
    wsClient.stream.listen((message) {
      try {
        final payload = jsonDecode(message);
        final event = payload['event'];
        final data = payload['data'];

        if (event == 'incident_update' || event == 'new_incident' || event == 'incident') {
          final newIncident = Incident.fromJson(data);
          _updateOrAddIncident(newIncident);
        } 
        else if (event == 'new_signal') {
          // CREATE A TEMPORARY INCIDENT FROM THE SIGNAL FOR IMMEDIATE FEEDBACK
          final signalData = data;
          final tempIncident = Incident(
            incidentId: signalData['signal_id'],
            status: 'detecting',
            location: IncidentLocation(
              lat: signalData['location']['lat'],
              lng: signalData['location']['lng'],
              areaName: signalData['location']['area_name'],
            ),
            classification: CrisisClassification(
              crisisType: signalData['crisis_type_hint'] ?? 'unknown',
              severity: 1,
              confidence: signalData['urgency_score'] ?? 0.5,
              reasoning: 'New signal detected: ${signalData['raw_content']}',
            ),
            signalIds: [signalData['signal_id']],
            createdAt: DateTime.now(),
            updatedAt: DateTime.now(),
            pipelineStage: 'ingested',
          );
          _updateOrAddIncident(tempIncident);
        }
        else if (event == 'demo_reset') {
          state = [];
        }
      } catch (e) {
        print('[IncidentProvider] Error: $e');
      }
    });

    _fetchActiveIncidents();
  }

  Future<void> _fetchActiveIncidents() async {
    try {
      final response = await apiClient.getActiveIncidents();
      if (response.statusCode == 200) {
        final List<dynamic> data = response.data['incidents'];
        state = data.map((json) => Incident.fromJson(json)).toList();
      }
    } catch (e) {}
  }

  void _updateOrAddIncident(Incident incident) {
    final index = state.indexWhere((i) => i.incidentId == incident.incidentId);
    if (index != -1) {
      state = [
        for (int i = 0; i < state.length; i++)
          if (i == index) incident else state[i]
      ];
    } else {
      state = [incident, ...state];
    }
  }
}

final incidentProvider = StateNotifierProvider<IncidentNotifier, List<Incident>>((ref) {
  return IncidentNotifier();
});
