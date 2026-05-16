import 'package:freezed_annotation/freezed_annotation.dart';

class SignalLocation {
  final double lat;
  final double lng;
  final String areaName;
  final String precision;

  SignalLocation({
    required this.lat,
    required this.lng,
    required this.areaName,
    this.precision = 'medium',
  });

  factory SignalLocation.fromJson(Map<String, dynamic> json) {
    return SignalLocation(
      lat: (json['lat'] as num).toDouble(),
      lng: (json['lng'] as num).toDouble(),
      areaName: json['area_name'] as String,
      precision: json['precision'] as String? ?? 'medium',
    );
  }

  Map<String, dynamic> toJson() => {
    'lat': lat,
    'lng': lng,
    'area_name': areaName,
    'precision': precision,
  };
}

class VelocityContext {
  final int mentionsLast5min;
  final String trend;

  VelocityContext({
    this.mentionsLast5min = 0,
    this.trend = 'stable',
  });

  factory VelocityContext.fromJson(Map<String, dynamic> json) {
    return VelocityContext(
      mentionsLast5min: json['mentions_last_5min'] as int? ?? 0,
      trend: json['trend'] as String? ?? 'stable',
    );
  }

  Map<String, dynamic> toJson() => {
    'mentions_last_5min': mentionsLast5min,
    'trend': trend,
  };
}

class NormalizedSignal {
  final String signalId;
  final String sourceType;
  final String sourceName;
  final String rawContent;
  final List<String> extractedKeywords;
  final String? crisisTypeHint;
  final SignalLocation location;
  final DateTime timestamp;
  final double urgencyScore;
  final double credibilityScore;
  final VelocityContext velocityContext;
  final bool processed;

  NormalizedSignal({
    required this.signalId,
    required this.sourceType,
    required this.sourceName,
    required this.rawContent,
    required this.extractedKeywords,
    this.crisisTypeHint,
    required this.location,
    required this.timestamp,
    this.urgencyScore = 0.5,
    this.credibilityScore = 0.5,
    required this.velocityContext,
    this.processed = false,
  });

  factory NormalizedSignal.fromJson(Map<String, dynamic> json) {
    return NormalizedSignal(
      signalId: json['signal_id'] as String,
      sourceType: json['source_type'] as String,
      sourceName: json['source_name'] as String,
      rawContent: json['raw_content'] as String,
      extractedKeywords: List<String>.from(json['extracted_keywords'] ?? []),
      crisisTypeHint: json['crisis_type_hint'] as String?,
      location: SignalLocation.fromJson(json['location'] as Map<String, dynamic>),
      timestamp: DateTime.parse(json['timestamp'] as String),
      urgencyScore: (json['urgency_score'] as num?)?.toDouble() ?? 0.5,
      credibilityScore: (json['credibility_score'] as num?)?.toDouble() ?? 0.5,
      velocityContext: VelocityContext.fromJson(json['velocity_context'] as Map<String, dynamic>),
      processed: json['processed'] as bool? ?? false,
    );
  }

  Map<String, dynamic> toJson() => {
    'signal_id': signalId,
    'source_type': sourceType,
    'source_name': sourceName,
    'raw_content': rawContent,
    'extracted_keywords': extractedKeywords,
    'crisis_type_hint': crisisTypeHint,
    'location': location.toJson(),
    'timestamp': timestamp.toIso8601String(),
    'urgency_score': urgencyScore,
    'credibility_score': credibilityScore,
    'velocity_context': velocityContext.toJson(),
    'processed': processed,
  };
}
