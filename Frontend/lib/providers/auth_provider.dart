import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../core/config/api_config.dart';
import '../core/network/api_client.dart';
import '../models/user_model.dart';
import '../services/push_notification_service.dart';

enum AutoLoginResult { authenticated, noSession, expired, retryable }

class AuthProvider with ChangeNotifier {
  String? _token;
  UserModel? _user;
  bool _isLoading = false;
  String? _errorMessage;
  Future<AutoLoginResult>? _autoLoginInFlight;

  String? get token => _token;
  UserModel? get user => _user;
  bool get isLoading => _isLoading;
  String? get errorMessage => _errorMessage;

  ApiClient get _apiClient => ApiClient(token: _token);

  /// 동시 호출은 진행 중인 시도에 합류하고, 끝난 뒤에는 다시 시도할 수 있습니다.
  Future<AutoLoginResult> tryAutoLogin() {
    return _autoLoginInFlight ??=
        _runAutoLogin().whenComplete(() => _autoLoginInFlight = null);
  }

  Future<AutoLoginResult> _runAutoLogin() async {
    final prefs = await SharedPreferences.getInstance();
    final savedToken = prefs.getString('jwt_token');
    if (savedToken == null || savedToken.isEmpty) {
      notifyListeners();
      return AutoLoginResult.noSession;
    }

    _token = savedToken;
    try {
      // 스플래시가 시도를 버리지 않도록 시간 제한은 이 안쪽에서 겁니다.
      await fetchMe().timeout(const Duration(seconds: 5));
      return AutoLoginResult.authenticated;
    } on ApiException catch (e) {
      // 401(토큰 만료/무효)만 세션을 정리하고, 네트워크·서버 오류는 토큰을 보존합니다.
      if (e.statusCode == 401) {
        await logout();
        return AutoLoginResult.expired;
      }
      _errorMessage = e.message;
      notifyListeners();
      return AutoLoginResult.retryable;
    } on TimeoutException {
      _errorMessage = '서버 응답이 지연되고 있습니다. 잠시 후 다시 시도해 주세요.';
      notifyListeners();
      return AutoLoginResult.retryable;
    } catch (e) {
      _errorMessage = e.toString();
      notifyListeners();
      return AutoLoginResult.retryable;
    }
  }

  Future<void> login(String name, String password) async {
    _setLoading(true);
    _errorMessage = null;

    try {
      final res = await ApiClient().post(
        ApiConfig.authLogin,
        body: {'name': name, 'password': password},
      );
      final tokenData = TokenResponse.fromJson(res);
      _token = tokenData.accessToken;

      final prefs = await SharedPreferences.getInstance();
      await prefs.setString('jwt_token', _token!);

      await fetchMe();
    } catch (e) {
      _errorMessage = e.toString();
      rethrow;
    } finally {
      _setLoading(false);
    }
  }

  Future<void> register(String email, String name, String password) async {
    _setLoading(true);
    _errorMessage = null;

    try {
      final res = await ApiClient().post(
        ApiConfig.authRegister,
        body: {'email': email, 'name': name, 'password': password},
      );
      final tokenData = TokenResponse.fromJson(res);
      _token = tokenData.accessToken;

      final prefs = await SharedPreferences.getInstance();
      await prefs.setString('jwt_token', _token!);

      await fetchMe();
    } catch (e) {
      _errorMessage = e.toString();
      rethrow;
    } finally {
      _setLoading(false);
    }
  }

  Future<void> fetchMe() async {
    if (_token == null) return;
    try {
      final res = await _apiClient.get(ApiConfig.authMe);
      _user = UserModel.fromJson(res);
      notifyListeners();
      await _syncDeviceToken();
    } catch (e) {
      _errorMessage = e.toString();
      rethrow;
    }
  }

  Future<void> _syncDeviceToken() async {
    try {
      final deviceToken = await PushNotificationService.instance.getToken();
      if (deviceToken == null || deviceToken.isEmpty) return;
      if (_user?.deviceToken == deviceToken) return;
      await updateDeviceToken(deviceToken);
    } catch (e) {
      // Ignored if device token sync fails
    }
  }

  Future<void> updateDeviceToken(String deviceToken) async {
    if (_token == null) return;
    try {
      final res = await _apiClient.patch(
        ApiConfig.authDeviceToken,
        body: {'device_token': deviceToken},
      );
      _user = UserModel.fromJson(res);
      notifyListeners();
    } catch (e) {
      _errorMessage = e.toString();
      rethrow;
    }

  }

  Future<void> updateNotificationsEnabled(bool enabled) async {
    if (_token == null || _user == null) return;
    try {
      final res = await _apiClient.patch(
        ApiConfig.authMe,
        body: {'notifications_enabled': enabled},
      );
      _user = UserModel.fromJson(res);
      notifyListeners();
    } catch (e) {
      _errorMessage = e.toString();
      rethrow;
    }
  }


  Future<void> logout() async {
    _token = null;
    _user = null;
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove('jwt_token');
    notifyListeners();
  }

  void _setLoading(bool value) {
    _isLoading = value;
    notifyListeners();
  }
}
