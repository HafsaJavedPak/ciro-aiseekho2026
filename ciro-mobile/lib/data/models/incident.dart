class IncidentLocation {
  final double lat;
  final double lng;
  final String areaName;
  final double affectedRadiusKm;

  IncidentLocation({
    required this.lat,
    required this.lng,
    required this.areaName,
    this.affectedRadiusKm = 0.5,
  });

  factory IncidentLocation.fromJson(Map<String, dynamic> json) {
    return IncidentLocation(
      lat: (json['lat'] as num).toDouble(),
      lng: (json['lng'] as num).toDouble(),
      areaName: json['area_name'] as String,
      affectedRadiusKm: (json['affected_radius_km'] as num?)?.toDouble() ?? 0.5,
    );
  }

  Map<String, dynamic> toJson() => {
    'lat': lat,
    'lng': lng,
    'area_name': areaName,
    'affected_radius_km': affectedRadiusKm,
  };
}

class CrisisClassification {
  final String crisisType;
  final int severity;
  final double confidence;
  final String reasoning;
  final String? counterHypothesis;
  final double? counterConfidence;
  final int affectedPopulation;

  CrisisClassification({
    required this.crisisType,
    required this.severity,
    required this.confidence,
    required this.reasoning,
    this.counterHypothesis,
    this.counterConfidence,
    this.affectedPopulation = 0,
  });

  factory CrisisClassification.fromJson(Map<String, dynamic> json) {
    return CrisisClassification(
      crisisType: json['crisis_type'] as String,
      severity: json['severity'] as int,
      confidence: (json['confidence'] as num).toDouble(),
      reasoning: json['reasoning'] as String,
      counterHypothesis: json['counter_hypothesis'] as String?,
      counterConfidence: (json['counter_confidence'] as num?)?.toDouble(),
      affectedPopulation: json['affected_population'] as int? ?? 0,
    );
  }

  Map<String, dynamic> toJson() => {
    'crisis_type': crisisType,
    'severity': severity,
    'confidence': confidence,
    'reasoning': reasoning,
    'counter_hypothesis': counterHypothesis,
    'counter_confidence': counterConfidence,
    'affected_population': affectedPopulation,
  };
}

class Incident {
  final String incidentId;
  final String status;
  final IncidentLocation location;
  final CrisisClassification? classification;
  final List<String> signalIds;
  final int signalCount;
  final DateTime createdAt;
  final DateTime updatedAt;
  final String pipelineStage;

  Incident({
    required this.incidentId,
    required this.status,
    required this.location,
    this.classification,
    required this.signalIds,
    this.signalCount = 0,
    required this.createdAt,
    required this.updatedAt,
    this.pipelineStage = 'ingested',
  });

  factory Incident.fromJson(Map<String, dynamic> json) {
    return Incident(
      incidentId: json['incident_id'] as String,
      status: json['status'] as String,
      location: IncidentLocation.fromJson(json['location'] as Map<String, dynamic>),
      classification: json['classification'] != null
          ? CrisisClassification.fromJson(json['classification'] as Map<String, dynamic>)
          : null,
      signalIds: List<String>.from(json['signal_ids'] ?? []),
      signalCount: json['signal_count'] as int? ?? 0,
      createdAt: DateTime.parse(json['created_at'] as String),
      updatedAt: DateTime.parse(json['updated_at'] as String),
      pipelineStage: json['pipeline_stage'] as String? ?? 'ingested',
    );
  }

  Map<String, dynamic> toJson() => {
    'incident_id': incidentId,
    'status': status,
    'location': location.toJson(),
    'classification': classification?.toJson(),
    'signal_ids': signalIds,
    'signal_count': signalCount,
    'created_at': createdAt.toIso8601String(),
    'updated_at': updatedAt.toIso8601String(),
    'pipeline_stage': pipelineStage,
  };
}
