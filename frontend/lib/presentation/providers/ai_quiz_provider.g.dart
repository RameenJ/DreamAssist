// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'ai_quiz_provider.dart';

// **************************************************************************
// RiverpodGenerator
// **************************************************************************

// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, type=warning
/// AI Quiz state notifier

@ProviderFor(AiQuiz)
final aiQuizProvider = AiQuizProvider._();

/// AI Quiz state notifier
final class AiQuizProvider extends $NotifierProvider<AiQuiz, AiQuizState> {
  /// AI Quiz state notifier
  AiQuizProvider._()
    : super(
        from: null,
        argument: null,
        retry: null,
        name: r'aiQuizProvider',
        isAutoDispose: true,
        dependencies: null,
        $allTransitiveDependencies: null,
      );

  @override
  String debugGetCreateSourceHash() => _$aiQuizHash();

  @$internal
  @override
  AiQuiz create() => AiQuiz();

  /// {@macro riverpod.override_with_value}
  Override overrideWithValue(AiQuizState value) {
    return $ProviderOverride(
      origin: this,
      providerOverride: $SyncValueProvider<AiQuizState>(value),
    );
  }
}

String _$aiQuizHash() => r'8eac4b1197d3f6bc924f328cab5443b50c4896fc';

/// AI Quiz state notifier

abstract class _$AiQuiz extends $Notifier<AiQuizState> {
  AiQuizState build();
  @$mustCallSuper
  @override
  void runBuild() {
    final ref = this.ref as $Ref<AiQuizState, AiQuizState>;
    final element =
        ref.element
            as $ClassProviderElement<
              AnyNotifier<AiQuizState, AiQuizState>,
              AiQuizState,
              Object?,
              Object?
            >;
    element.handleCreate(ref, build);
  }
}
