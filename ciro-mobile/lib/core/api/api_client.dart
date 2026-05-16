import 'package:dio/dio.dart';
import '../constants/constants.dart';

class ApiClient {
  late final Dio _dio;

  ApiClient() {
    _dio = Dio(BaseOptions(
      baseUrl: AppConstants.baseUrl,
      connectTimeout: const Duration(seconds: 15),
      receiveTimeout: const Duration(seconds: 10),
    ));
  }

  Future<Response> getActiveIncidents() async {
    return await _dio.get(AppConstants.incidentsActive);
  }

  Future<Response> getIncidentTraces(String incidentId) async {
    return await _dio.get(AppConstants.incidentTraces.replaceFirst('%s', incidentId));
  }

  Future<Response> ingestSignal(Map<String, dynamic> rawSignal) async {
    return await _dio.post(AppConstants.signalIngest, data: rawSignal);
  }
}

final apiClient = ApiClient();
