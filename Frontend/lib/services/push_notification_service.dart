import 'dart:io';

import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';

@pragma('vm:entry-point')
Future<void> firebaseMessagingBackgroundHandler(RemoteMessage message) async {
  // Background notification messages are displayed by Android automatically.
}

class PushNotificationService {
  PushNotificationService._();

  static final PushNotificationService instance = PushNotificationService._();

  final FirebaseMessaging _messaging = FirebaseMessaging.instance;
  final FlutterLocalNotificationsPlugin _localNotifications =
      FlutterLocalNotificationsPlugin();

  Future<void> initialize() async {
    if (!Platform.isAndroid) return;

    try {
      await _messaging
          .requestPermission(
            alert: true,
            badge: true,
            sound: true,
          )
          .timeout(const Duration(seconds: 2));
    } catch (e) {

    }

    try {
      const channel = AndroidNotificationChannel(
        'routine_notifications',
        '루틴 알림',
        description: '출발 및 실시간 대중교통 알림',
        importance: Importance.high,
      );
      await _localNotifications
          .resolvePlatformSpecificImplementation<
              AndroidFlutterLocalNotificationsPlugin>()
          ?.createNotificationChannel(channel);

      const androidSettings =
          AndroidInitializationSettings('@mipmap/ic_launcher');
      await _localNotifications.initialize(
        const InitializationSettings(android: androidSettings),
      );

      FirebaseMessaging.onMessage.listen(_showForegroundNotification);
      FirebaseMessaging.onBackgroundMessage(firebaseMessagingBackgroundHandler);
    } catch (e) {

    }
  }

  Future<String?> getToken() async {
    if (!Platform.isAndroid) return null;
    try {
      return await _messaging.getToken().timeout(const Duration(seconds: 2));
    } catch (e) {
      return null;
    }
  }

  Future<void> _showForegroundNotification(RemoteMessage message) async {
    final notification = message.notification;
    if (notification == null) return;

    await _localNotifications.show(
      notification.hashCode,
      notification.title,
      notification.body,
      const NotificationDetails(
        android: AndroidNotificationDetails(
          'routine_notifications',
          '루틴 알림',
          channelDescription: '출발 및 실시간 대중교통 알림',
          importance: Importance.high,
          priority: Priority.high,
          icon: '@mipmap/ic_launcher',
        ),
      ),
    );
  }
}
