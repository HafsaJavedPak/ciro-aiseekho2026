import 'dart:convert';
import 'package:web_socket_channel/web_socket_channel.dart';
import '../constants/constants.dart';

class WebSocketClient {
  WebSocketChannel? _channel;
  bool _isConnected = false;

  Stream<dynamic> get stream => _channel?.stream ?? const Stream.empty();

  void connect() {
    if (_isConnected) return;
    
    try {
      _channel = WebSocketChannel.connect(Uri.parse(AppConstants.wsUrl));
      _isConnected = true;
      print('[WS] Connected to ${AppConstants.wsUrl}');
    } catch (e) {
      print('[WS] Connection failed: $e');
      _isConnected = false;
    }
  }

  void disconnect() {
    _channel?.sink.close();
    _isConnected = false;
    print('[WS] Disconnected');
  }

  void send(dynamic message) {
    if (_isConnected) {
      _channel?.sink.add(jsonEncode(message));
    }
  }
}

final wsClient = WebSocketClient();
