// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'ai_study_tools_provider.dart';

// **************************************************************************
// RiverpodGenerator
// **************************************************************************

// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, type=warning
/// Study tools state notifier

@ProviderFor(StudyTools)
final studyToolsProvider = StudyToolsProvider._();

/// Study tools state notifier
final class StudyToolsProvider
    extends $NotifierProvider<StudyTools, StudyToolsState> {
  /// Study tools state notifier
  StudyToolsProvider._()
    : super(
        from: null,
        argument: null,
        retry: null,
        name: r'studyToolsProvider',
        isAutoDispose: true,
        dependencies: null,
        $allTransitiveDependencies: null,
      );

  @override
  String debugGetCreateSourceHash() => _$studyToolsHash();

  @$internal
  @override
  StudyTools create() => StudyTools();

  /// {@macro riverpod.override_with_value}
  Override overrideWithValue(StudyToolsState value) {
    return $ProviderOverride(
      origin: this,
      providerOverride: $SyncValueProvider<StudyToolsState>(value),
    );
  }
}

String _$studyToolsHash() => r'a842740dcf3b860b9c737dbeab3f3c785fce5d3f';

/// Study tools state notifier

abstract class _$StudyTools extends $Notifier<StudyToolsState> {
  StudyToolsState build();
  @$mustCallSuper
  @override
  void runBuild() {
    final ref = this.ref as $Ref<StudyToolsState, StudyToolsState>;
    final element =
        ref.element
            as $ClassProviderElement<
              AnyNotifier<StudyToolsState, StudyToolsState>,
              StudyToolsState,
              Object?,
              Object?
            >;
    element.handleCreate(ref, build);
  }
}
