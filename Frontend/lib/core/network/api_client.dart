import 'dart:convert';
import 'package:http/http.dart' as http;
import '../config/api_config.dart';

class ApiException implements Exception {
  final String message;
  final int? statusCode;

  ApiException(this.message, {this.statusCode});

  @override
  String toString() => message;
}

class ApiClient {
  final String? token;

  ApiClient({this.token});

  Map<String, String> get _headers {
    final headers = <String, String>{
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    };
    if (token != null && token!.isNotEmpty) {
      headers['Authorization'] = 'Bearer $token';
    }
    return headers;
  }

  Uri _uri(String path, [Map<String, dynamic>? queryParameters]) {
    final urlString = '${ApiConfig.baseUrl}$path';
    return Uri.parse(urlString).replace(
      queryParameters: queryParameters?.map(
        (key, value) => MapEntry(key, value.toString()),
      ),
    );
  }

  dynamic _processResponse(http.Response response) {
    final responseBody = response.body.isNotEmpty
        ? json.decode(utf8.decode(response.bodyBytes))
        : null;

    if (response.statusCode >= 200 && response.statusCode < 300) {
      return responseBody;
    } else {
      String errorMessage = '서버 오류가 발생했습니다 (${response.statusCode})';
      if (responseBody is Map && responseBody.containsKey('detail')) {
        final detail = responseBody['detail'];
        if (detail is String) {
          errorMessage = detail;
        } else if (detail is List) {
          errorMessage = detail.map((e) => e['msg'] ?? e.toString()).join('\n');
        }
      }
      throw ApiException(errorMessage, statusCode: response.statusCode);
    }
  }

  Future<dynamic> get(String path, {Map<String, dynamic>? queryParams}) async {
    try {
      final response = await http
          .get(_uri(path, queryParams), headers: _headers)
          .timeout(const Duration(seconds: 15));
      return _processResponse(response);
    } catch (e) {
      if (e is ApiException) rethrow;
      throw ApiException('네트워크 연결을 확인해주세요: $e');
    }
  }

  Future<dynamic> post(String path, {dynamic body}) async {
    try {
      final response = await http
          .post(
            _uri(path),
            headers: _headers,
            body: body != null ? json.encode(body) : null,
          )
          .timeout(const Duration(seconds: 20));
      return _processResponse(response);
    } catch (e) {
      if (e is ApiException) rethrow;
      throw ApiException('네트워크 연결을 확인해주세요: $e');
    }
  }

  Future<dynamic> put(String path, {dynamic body}) async {
    try {
      final response = await http
          .put(
            _uri(path),
            headers: _headers,
            body: body != null ? json.encode(body) : null,
          )
          .timeout(const Duration(seconds: 20));
      return _processResponse(response);
    } catch (e) {
      if (e is ApiException) rethrow;
      throw ApiException('네트워크 연결을 확인해주세요: $e');
    }
  }

  Future<dynamic> patch(String path, {dynamic body}) async {
    try {
      final response = await http
          .patch(
            _uri(path),
            headers: _headers,
            body: body != null ? json.encode(body) : null,
          )
          .timeout(const Duration(seconds: 15));
      return _processResponse(response);
    } catch (e) {
      if (e is ApiException) rethrow;
      throw ApiException('네트워크 연결을 확인해주세요: $e');
    }
  }

  Future<dynamic> delete(String path) async {
    try {
      final response = await http
          .delete(_uri(path), headers: _headers)
          .timeout(const Duration(seconds: 15));
      return _processResponse(response);
    } catch (e) {
      if (e is ApiException) rethrow;
      throw ApiException('네트워크 연결을 확인해주세요: $e');
    }
  }
}
