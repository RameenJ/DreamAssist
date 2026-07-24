import 'package:riverpod_annotation/riverpod_annotation.dart';
import '../../data/models/subject_model.dart';
import '../../data/services/subject_api_service.dart';
import '../../core/providers/app_providers.dart';

part 'subject_provider.g.dart';

/// Subject state
class SubjectState {
  final List<SubjectModel> subjects;
  final bool isLoading;
  final String? error;

  const SubjectState({
    this.subjects = const [],
    this.isLoading = false,
    this.error,
  });

  SubjectState copyWith({
    List<SubjectModel>? subjects,
    bool? isLoading,
    String? error,
  }) {
    return SubjectState(
      subjects: subjects ?? this.subjects,
      isLoading: isLoading ?? this.isLoading,
      error: error,
    );
  }
}

/// Subject state notifier
@riverpod
class Subject extends _$Subject {
  @override
  SubjectState build() {
    return const SubjectState();
  }

  SubjectApiService get _subjectService => ref.watch(subjectApiServiceProvider);

  /// Fetch all subjects
  Future<void> fetchSubjects() async {
    state = state.copyWith(isLoading: true, error: null);

    final result = await _subjectService.getSubjects();
    result.when(
      success: (subjects) {
        state = state.copyWith(subjects: subjects, isLoading: false);
      },
      failure: (message) {
        state = state.copyWith(isLoading: false, error: message);
      },
    );
  }

  /// Create a new subject
  Future<bool> createSubject(String name) async {
    final request = SubjectCreateRequest(name: name);
    final result = await _subjectService.createSubject(request);

    return result.when(
      success: (subject) {
        state = state.copyWith(subjects: [...state.subjects, subject]);
        return true;
      },
      failure: (message) {
        state = state.copyWith(error: message);
        return false;
      },
    );
  }

  /// Update a subject
  Future<bool> updateSubject(String subjectId, String newName) async {
    final request = SubjectUpdateRequest(name: newName);
    final result = await _subjectService.updateSubject(subjectId, request);

    return result.when(
      success: (updatedSubject) {
        final updatedSubjects = state.subjects.map((subj) {
          return subj.id == subjectId ? updatedSubject : subj;
        }).toList();
        state = state.copyWith(subjects: updatedSubjects);
        return true;
      },
      failure: (message) {
        state = state.copyWith(error: message);
        return false;
      },
    );
  }

  /// Delete a subject
  Future<bool> deleteSubject(String subjectId) async {
    final result = await _subjectService.deleteSubject(subjectId);

    return result.when(
      success: (_) {
        final updatedSubjects = state.subjects
            .where((subj) => subj.id != subjectId)
            .toList();
        state = state.copyWith(subjects: updatedSubjects);
        return true;
      },
      failure: (message) {
        state = state.copyWith(error: message);
        return false;
      },
    );
  }

  /// Clear error
  void clearError() {
    state = state.copyWith(error: null);
  }
}
