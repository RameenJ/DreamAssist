// This is a basic Flutter widget test for DreamAssist.
//
// To perform an interaction with a widget in your test, use the WidgetTester
// utility in the flutter_test package. For example, you can send tap and scroll
// gestures. You can also use WidgetTester to find child widgets in the widget
// tree, read text, and verify that the values of widget properties are correct.

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:mockito/mockito.dart';
import 'package:dream_assist/presentation/screens/auth/login_screen.dart';
import 'package:dream_assist/presentation/providers/auth_provider.dart';

// Create a mock auth provider
class MockAuth extends Mock implements Auth {}

void main() {
  testWidgets('Login screen renders correctly', (WidgetTester tester) async {
    // Build the login screen wrapped in necessary providers with overrides
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          authProvider.overrideWithValue(const AuthState()),
        ],
        child: const MaterialApp(
          home: LoginScreen(),
        ),
      ),
    );

    // Wait for all animations and async operations
    await tester.pumpAndSettle();

    // Verify that key elements are present
    expect(find.text('DreamAssist'), findsOneWidget);
    expect(find.text('Your AI-Powered Learning Companion'), findsOneWidget);
    expect(find.text('Email'), findsOneWidget);
    expect(find.text('Password'), findsOneWidget);
    expect(find.text('Login'), findsOneWidget);
    expect(find.text('Sign Up'), findsOneWidget);
  });

  testWidgets('Login screen has email and password fields', (WidgetTester tester) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          authProvider.overrideWithValue(const AuthState()),
        ],
        child: const MaterialApp(
          home: LoginScreen(),
        ),
      ),
    );

    await tester.pumpAndSettle();

    // Verify form fields exist
    expect(find.byType(TextFormField), findsNWidgets(2)); // Email and password
  });
}
