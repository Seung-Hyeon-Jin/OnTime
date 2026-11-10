import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../core/config/api_config.dart';
import '../core/network/api_client.dart';
import '../models/user_model.dart';
import '../services/push_notification_service.dart';

class AuthProvider with ChangeNotifier {
  String? _token;
  UserModel? _user;
  bool _isLoading = false;
  String? _errorMessage;
  bool _isAutoLoginDone = false;

  String? get token => _token;
  UserModel? get user => _user;
  bool get isAuth => _token != null && _token!.isNotEmpty;
  bool get isLoading => _isLoading;
  String? get errorMessage => _errorMessage;
  bool get isAutoLoginDone => _isAutoLoginDone;

  ApiClient get _apiClient => ApiClient(token: _token);

  Future<bool> tryAutoLogin() async {
    if (_isAutoLoginDone) return isAuth;

    final prefs = await SharedPreferences.getInstance();
    if (!prefs.containsKey('jwt_token')) {
      _isAutoLoginDone = true;
      notifyListeners();
      return false;
    }

    _token = prefs.getString('jwt_token');
    try {
      await fetchMe();
      _isAutoLoginDone = true;
      notifyListeners();
      return true;
    } catch (_) {
      await logout();
      _isAutoLoginDone = true;
      notifyListeners();
      return false;
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

  Future<void> sendTestNotification() async {
    if (_token == null) return;
    try {
      await _apiClient.post(ApiConfig.authTestNotification);
    } catch (e) {
      _errorMessage = e.toString();
      rethrow;
    }
  }

  Future<void> logout() async {
    _token = null;
    _user = null;
    _isAutoLoginDone = true;
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove('jwt_token');
    notifyListeners();
  }

  void _setLoading(bool value) {
    _isLoading = value;
    notifyListeners();
  }
}
