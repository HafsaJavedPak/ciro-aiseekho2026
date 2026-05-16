class AppConstants {
  // Using physical PC IP for mobile device connectivity
  static const String baseUrl = 'http://192.168.1.17:8000';
  static const String wsUrl = 'ws://192.168.1.17:8000/ws';
  
  static const String incidentsActive = '/incidents/active';
  static const String incidentTraces = '/incidents/%s/traces';
  static const String signalIngest = '/signals/ingest';
}
