// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'mood_provider.dart';

// **************************************************************************
// RiverpodGenerator
// **************************************************************************

// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, type=warning
/// Mood logging state notifier

@ProviderFor(Mood)
final moodProvider = MoodProvider._();

/// Mood logging state notifier
final class MoodProvider extends $NotifierProvider<Mood, MoodState> {
  /// Mood logging state notifier
  MoodProvider._()
    : super(
        from: null,
        argument: null,
        retry: null,
        name: r'moodProvider',
        isAutoDispose: true,
        dependencies: null,
        $allTransitiveDependencies: null,
      );

  @override
  String debugGetCreateSourceHash() => _$moodHash();

  @$internal
  @override
  Mood create() => Mood();

  /// {@macro riverpod.override_with_value}
  Override overrideWithValue(MoodState value) {
    return $ProviderOverride(
      origin: this,
      providerOverride: $SyncValueProvider<MoodState>(value),
    );
  }
}

String _$moodHash() => r'647d4a159adf3e4d185d0b77749d4448163e741b';

/// Mood logging state notifier

abstract class _$Mood extends $Notifier<MoodState> {
  MoodState build();
  @$mustCallSuper
  @override
  void runBuild() {
    final ref = this.ref as $Ref<MoodState, MoodState>;
    final element =
        ref.element
            as $ClassProviderElement<
              AnyNotifier<MoodState, MoodState>,
              MoodState,
              Object?,
              Object?
            >;
    element.handleCreate(ref, build);
  }
}

/// Notifier for managing mood history

@ProviderFor(MoodHistory)
final moodHistoryProvider = MoodHistoryProvider._();

/// Notifier for managing mood history
final class MoodHistoryProvider
    extends $NotifierProvider<MoodHistory, MoodHistoryState> {
  /// Notifier for managing mood history
  MoodHistoryProvider._()
    : super(
        from: null,
        argument: null,
        retry: null,
        name: r'moodHistoryProvider',
        isAutoDispose: true,
        dependencies: null,
        $allTransitiveDependencies: null,
      );

  @override
  String debugGetCreateSourceHash() => _$moodHistoryHash();

  @$internal
  @override
  MoodHistory create() => MoodHistory();

  /// {@macro riverpod.override_with_value}
  Override overrideWithValue(MoodHistoryState value) {
    return $ProviderOverride(
      origin: this,
      providerOverride: $SyncValueProvider<MoodHistoryState>(value),
    );
  }
}

String _$moodHistoryHash() => r'82d3b4c06b88b55c4a6240dbe99f0fea8a74dbe4';

/// Notifier for managing mood history

abstract class _$MoodHistory extends $Notifier<MoodHistoryState> {
  MoodHistoryState build();
  @$mustCallSuper
  @override
  void runBuild() {
    final ref = this.ref as $Ref<MoodHistoryState, MoodHistoryState>;
    final element =
        ref.element
            as $ClassProviderElement<
              AnyNotifier<MoodHistoryState, MoodHistoryState>,
              MoodHistoryState,
              Object?,
              Object?
            >;
    element.handleCreate(ref, build);
  }
}
