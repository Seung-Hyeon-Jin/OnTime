import 'package:flutter_test/flutter_test.dart';
import 'package:transport_app_frontend/models/arrival_model.dart';

void main() {
  group('ArrivalItem formattedArrival 지하철 파싱 테스트', () {
    test('전역 도착 메시지는 "곧 도착"으로 바뀌지 않고 "전역 도착"을 유지해야 함', () {
      final item = ArrivalItem(
        transportType: 'SUBWAY',
        stationOrStopName: '수원',
        arrivalMessage: '전역 도착',
        arrivalSeconds: null,
      );

      expect(item.formattedArrival, '전역 도착');
    });

    test('전역 출발 메시지는 "전역 출발"을 유지해야 함', () {
      final item = ArrivalItem(
        transportType: 'SUBWAY',
        stationOrStopName: '수원',
        arrivalMessage: '전역 출발',
        arrivalSeconds: null,
      );

      expect(item.formattedArrival, '전역 출발');
    });

    test('수원 도착 / 당역 도착 등 전역 미포함 도착 메시지는 "곧 도착"으로 표시됨', () {
      final item = ArrivalItem(
        transportType: 'SUBWAY',
        stationOrStopName: '수원',
        arrivalMessage: '수원 도착',
        arrivalSeconds: null,
      );

      expect(item.formattedArrival, '곧 도착');
    });

    test('[N]번째 전역 형식은 "N전역 (역명)" 형식으로 포맷팅됨', () {
      final item = ArrivalItem(
        transportType: 'SUBWAY',
        stationOrStopName: '수원',
        arrivalMessage: '[6]번째 전역 (청명)',
        arrivalSeconds: null,
      );

      expect(item.formattedArrival, '6전역 (청명)');
    });
  });
}
