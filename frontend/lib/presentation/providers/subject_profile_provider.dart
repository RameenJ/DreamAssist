import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../data/models/subject_profile_model.dart';
import '../../data/services/subject_profile_api_service.dart';
import '../../core/providers/app_providers.dart';

final subjectProfileApiServiceProvider = Provider<SubjectProfileApiService>((ref) {
  final dioClient = ref.watch(dioClientProvider);
  return SubjectProfileApiService(dioClient);
});

class SubjectProfileState {
  final List<SubjectProfileModel> profiles;
  final bool isLoading;
  final String? error;

  SubjectProfileState({
    this.profiles = const [],
    this.isLoading = false,
    this.error,
  });

  SubjectProfileState copyWith({
    List<SubjectProfileModel>? profiles,
    bool? isLoading,
    String? error,
  }) {
    return SubjectProfileState(
      profiles: profiles ?? this.profiles,
      isLoading: isLoading ?? this.isLoading,
      error: error,
    );
  }
}

class SubjectProfileNotifier extends Notifier<SubjectProfileState> {
  @override
  SubjectProfileState build() {
    return SubjectProfileState();
  }

  Future<void> loadProfiles() async {
    state = state.copyWith(isLoading: true, error: null);
    try {
      final apiService = ref.read(subjectProfileApiServiceProvider);
      final profiles = await apiService.getAllSubjectProfiles();
      if (!ref.mounted) return;
      state = state.copyWith(profiles: profiles, isLoading: false);
    } catch (e) {
      if (!ref.mounted) return;
      state = state.copyWith(
        isLoading: false,
        error: e.toString(),
      );
    }
  }

  Future<DiagnosticQuizResponse?> generateQuiz(String subject) async {
    try {
      final apiService = ref.read(subjectProfileApiServiceProvider);
      final result = await apiService.generateDiagnosticQuiz(subject);
      if (!ref.mounted) return null;
      return result;
    } catch (e) {
      if (!ref.mounted) return null;
      state = state.copyWith(error: e.toString());
      return null;
    }
  }

  Future<bool> submitQuizAnswers({
    required String subject,
    required List<String> answers,
  }) async {
    state = state.copyWith(isLoading: true, error: null);
    try {
      final apiService = ref.read(subjectProfileApiServiceProvider);
      final profile = await apiService.evaluateDiagnosticQuiz(
        subject: subject,
        answers: answers,
      );
      if (!ref.mounted) return false;
      // Add or update profile in state
      final updatedProfiles = [...state.profiles];
      final existingIndex =
          updatedProfiles.indexWhere((p) => p.subject == subject);
      if (existingIndex >= 0) {
        updatedProfiles[existingIndex] = profile;
      } else {
        updatedProfiles.add(profile);
      }
      state = state.copyWith(profiles: updatedProfiles, isLoading: false);
      return true;
    } catch (e) {
      if (!ref.mounted) return false;
      state = state.copyWith(
        isLoading: false,
        error: e.toString(),
      );
      return false;
    }
  }

  Future<bool> createProfileManually(SubjectProfileCreate profile) async {
    state = state.copyWith(isLoading: true, error: null);
    try {
      final apiService = ref.read(subjectProfileApiServiceProvider);
      final createdProfile =
          await apiService.createSubjectProfileManually(profile);
      if (!ref.mounted) return false;
      // Add or update profile in state
      final updatedProfiles = [...state.profiles];
      final existingIndex =
          updatedProfiles.indexWhere((p) => p.subject == profile.subject);
      if (existingIndex >= 0) {
        updatedProfiles[existingIndex] = createdProfile;
      } else {
        updatedProfiles.add(createdProfile);
      }
      state = state.copyWith(profiles: updatedProfiles, isLoading: false);
      return true;
    } catch (e) {
      if (!ref.mounted) return false;
      state = state.copyWith(
        isLoading: false,
        error: e.toString(),
      );
      return false;
    }
  }

  Future<bool> updateProfile({
    required String subject,
    String? level,
    String? studyPace,
    String? studyStyle,
    String? breakPreference,
  }) async {
    state = state.copyWith(isLoading: true, error: null);
    try {
      final apiService = ref.read(subjectProfileApiServiceProvider);
      final updatedProfile = await apiService.updateSubjectProfile(
        subject: subject,
        level: level,
        studyPace: studyPace,
        studyStyle: studyStyle,
        breakPreference: breakPreference,
      );
      if (!ref.mounted) return false;
      // Update profile in state
      final updatedProfiles = state.profiles.map((p) {
        if (p.subject == subject) {
          return updatedProfile;
        }
        return p;
      }).toList();
      state = state.copyWith(profiles: updatedProfiles, isLoading: false);
      return true;
    } catch (e) {
      if (!ref.mounted) return false;
      state = state.copyWith(
        isLoading: false,
        error: e.toString(),
      );
      return false;
    }
  }

  Future<bool> deleteProfile(String subject) async {
    state = state.copyWith(isLoading: true, error: null);
    try {
      final apiService = ref.read(subjectProfileApiServiceProvider);
      await apiService.deleteSubjectProfile(subject);
      if (!ref.mounted) return false;
      // Remove profile from state
      final updatedProfiles =
          state.profiles.where((p) => p.subject != subject).toList();
      state = state.copyWith(profiles: updatedProfiles, isLoading: false);
      return true;
    } catch (e) {
      if (!ref.mounted) return false;
      state = state.copyWith(
        isLoading: false,
        error: e.toString(),
      );
      return false;
    }
  }

  void clearError() {
    state = state.copyWith(error: null);
  }
}

final subjectProfileProvider =
    NotifierProvider<SubjectProfileNotifier, SubjectProfileState>(() {
  return SubjectProfileNotifier();
});

// Selector to get list of subject names for study planner
final userSubjectsProvider =
    FutureProvider<List<SubjectProfileModel>>((ref) async {
  final subjectState = ref.watch(subjectProfileProvider);
  
  // If no profiles loaded, try to load them
  if (subjectState.profiles.isEmpty) {
    try {
      final notifier = ref.read(subjectProfileProvider.notifier);
      await notifier.loadProfiles();
      // Return the updated profiles
      final updatedState = ref.watch(subjectProfileProvider);
      return updatedState.profiles;
    } catch (e) {
      return [];
    }
  }
  
  return subjectState.profiles;
});
