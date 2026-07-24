// frontend/lib/data/repositories/persona_repository.dart

import 'package:flutter/foundation.dart';
import 'package:dio/dio.dart';
import '../models/persona_models.dart';
import '../../core/services/dio_service.dart';

class PersonaRepository {
  final DioService _dioService;
  final String _baseUrl = '/api/personas';

  PersonaRepository({DioService? dioService})
      : _dioService = dioService ?? DioService();

  // ========================================================================
  // PERSONA MANAGEMENT APIS
  // ========================================================================

  /// Get all available personas with unlock status
  Future<List<Persona>> getAllPersonas() async {
    try {
      final response = await _dioService.get('$_baseUrl');
      
      if (response.statusCode == 200) {
        final List<dynamic> data = response.data ?? [];
        return data.map((json) => Persona.fromJson(json as Map<String, dynamic>)).toList();
      } else {
        throw Exception('Failed to fetch personas: ${response.statusMessage}');
      }
    } on DioException catch (e) {
      _handleDioError(e, 'getAllPersonas');
      rethrow;
    } catch (e) {
      debugPrint('❌ Error in getAllPersonas: $e');
      rethrow;
    }
  }

  /// Get only unlocked personas for current user
  Future<List<Persona>> getUnlockedPersonas() async {
    try {
      final response = await _dioService.get('$_baseUrl/unlocked');
      
      if (response.statusCode == 200) {
        final List<dynamic> data = response.data ?? [];
        return data.map((json) => Persona.fromJson(json as Map<String, dynamic>)).toList();
      } else {
        throw Exception('Failed to fetch unlocked personas: ${response.statusMessage}');
      }
    } on DioException catch (e) {
      _handleDioError(e, 'getUnlockedPersonas');
      rethrow;
    } catch (e) {
      debugPrint('❌ Error in getUnlockedPersonas: $e');
      rethrow;
    }
  }

  /// Get details of a specific persona
  Future<Persona> getPersonaDetails(String personaId) async {
    try {
      final response = await _dioService.get('$_baseUrl/$personaId');
      
      if (response.statusCode == 200) {
        return Persona.fromJson(response.data as Map<String, dynamic>);
      } else {
        throw Exception('Failed to fetch persona details: ${response.statusMessage}');
      }
    } on DioException catch (e) {
      _handleDioError(e, 'getPersonaDetails');
      rethrow;
    } catch (e) {
      debugPrint('❌ Error in getPersonaDetails: $e');
      rethrow;
    }
  }

  /// Select a persona for the user
  Future<bool> selectPersona(String personaId) async {
    try {
      final response = await _dioService.post(
        '$_baseUrl/select',
        data: {'persona_id': personaId},
      );
      
      if (response.statusCode == 200) {
        final data = response.data as Map<String, dynamic>;
        return data['success'] ?? false;
      } else {
        throw Exception('Failed to select persona: ${response.statusMessage}');
      }
    } on DioException catch (e) {
      _handleDioError(e, 'selectPersona');
      rethrow;
    } catch (e) {
      debugPrint('❌ Error in selectPersona: $e');
      rethrow;
    }
  }

  // ========================================================================
  // CHAT APIS
  // ========================================================================

  /// Chat with a persona
  /// 
  /// [message] - User's message
  /// [personaId] - Optional, uses selected if not provided
  /// [conversationId] - Optional, for continuing conversation
  Future<PersonaChatResponse> chatWithPersona({
    required String message,
    String? personaId,
    String? conversationId,
  }) async {
    try {
      final request = PersonaChatRequest(
        message: message,
        personaId: personaId,
        conversationId: conversationId,
      );

      final response = await _dioService.post(
        '$_baseUrl/chat',
        data: request.toJson(),
      );

      if (response.statusCode == 200) {
        return PersonaChatResponse.fromJson(response.data as Map<String, dynamic>);
      } else {
        throw Exception('Failed to get persona response: ${response.statusMessage}');
      }
    } on DioException catch (e) {
      _handleDioError(e, 'chatWithPersona');
      rethrow;
    } catch (e) {
      debugPrint('❌ Error in chatWithPersona: $e');
      rethrow;
    }
  }

  /// Get chat history with a specific persona
  Future<ChatHistoryResponse?> getChatHistory(String personaId) async {
    try {
      final response = await _dioService.get('$_baseUrl/chat-history/$personaId');
      
      if (response.statusCode == 200) {
        final data = response.data as Map<String, dynamic>;
        if (data['messages'] != null && data['messages'].isNotEmpty) {
          return ChatHistoryResponse.fromJson(data);
        }
        return null;
      } else {
        return null;  // No history found is not an error
      }
    } on DioException catch (e) {
      _handleDioError(e, 'getChatHistory');
      return null;
    } catch (e) {
      debugPrint('❌ Error in getChatHistory: $e');
      return null;
    }
  }

  // ========================================================================
  // HELPER METHODS
  // ========================================================================

  void _handleDioError(DioException error, String context) {
    if (error.type == DioExceptionType.connectionTimeout) {
      debugPrint('❌ [$context] Connection timeout');
    } else if (error.type == DioExceptionType.receiveTimeout) {
      debugPrint('❌ [$context] Receive timeout');
    } else if (error.response?.statusCode == 400) {
      debugPrint('❌ [$context] Bad request: ${error.response?.data}');
    } else if (error.response?.statusCode == 401) {
      debugPrint('❌ [$context] Unauthorized');
    } else if (error.response?.statusCode == 404) {
      debugPrint('❌ [$context] Not found');
    } else if (error.response?.statusCode == 500) {
      debugPrint('❌ [$context] Server error');
    } else {
      debugPrint('❌ [$context] Error: ${error.message}');
    }
  }
}
