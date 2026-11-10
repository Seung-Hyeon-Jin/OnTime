import 'dart:io';
import 'package:flutter/foundation.dart';

class ApiConfig {
  // Android 에뮬레이터에서는 10.0.2.2를 사용하기 위해 physicalPhoneIp를 null로 둡니다.
  // 실제 휴대폰 USB 연결 시에는 `adb reverse tcp:8000 tcp:8000`을 사용하거나 PC IP를 입력하세요.
  static String? physicalPhoneIp;

  static String get baseUrl {
    if (kIsWeb) {
      return 'http://127.0.0.1:8000';
    }
    if (physicalPhoneIp != null && physicalPhoneIp!.isNotEmpty) {
      return 'http://$physicalPhoneIp:8000';
    }
    if (Platform.isAndroid) {
      // 10.0.2.2 points to host machine from Android Emulator
      return 'http://10.0.2.2:8000';
    }
    return 'http://127.0.0.1:8000';
  }

  // Endpoints
  static const String authRegister = '/api/v1/auth/register';
  static const String authLogin = '/api/v1/auth/login';
  static const String authDeviceToken = '/api/v1/auth/me/device-token';
  static const String authMe = '/api/v1/auth/me';
  static const String authTestNotification =
      '/api/v1/auth/me/test-notification';

  static const String locationsSearch = '/api/v1/locations/search';
  static const String routesSearch = '/api/v1/routes/search';

  static const String arrivalsSubway = '/api/v1/arrivals/subway';
  static const String arrivalsBus = '/api/v1/arrivals/bus';
  static const String busStopsSearch = '/api/v1/arrivals/bus/stops';

  static const String routines = '/api/v1/routines';
  static String routineDetail(String id) => '/api/v1/routines/$id';
  static String routineExecute(String id) => '/api/v1/routines/$id/execute';
  static String routineTestNotification(String id) =>
      '/api/v1/routines/$id/test-notification';
}
