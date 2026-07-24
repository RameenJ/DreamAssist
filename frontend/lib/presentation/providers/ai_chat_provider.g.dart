// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'ai_chat_provider.dart';

// **************************************************************************
// RiverpodGenerator
// **************************************************************************

// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, type=warning
/// AI Chat state notifier

@ProviderFor(AiChat)
final aiChatProvider = AiChatProvider._();

/// AI Chat state notifier
final class AiChatProvider extends $NotifierProvider<AiChat, AiChatState> {
  /// AI Chat state notifier
  AiChatProvider._()
    : super(
        from: null,
        argument: null,
        retry: null,
        name: r'aiChatProvider',
        isAutoDispose: true,
        dependencies: null,
        $allTransitiveDependencies: null,
      );

  @override
  String debugGetCreateSourceHash() => _$aiChatHash();

  @$internal
  @override
  AiChat create() => AiChat();

  /// {@macro riverpod.override_with_value}
  Override overrideWithValue(AiChatState value) {
    return $ProviderOverride(
      origin: this,
      providerOverride: $SyncValueProvider<AiChatState>(value),
    );
  }
}

String _$aiChatHash() => r'3de4c9bb0e46e7893cb3d907d68f09976e6aa8be';

/// AI Chat state notifier

abstract class _$AiChat extends $Notifier<AiChatState> {
  AiChatState build();
  @$mustCallSuper
  @override
  void runBuild() {
    final ref = this.ref as $Ref<AiChatState, AiChatState>;
    final element =
        ref.element
            as $ClassProviderElement<
              AnyNotifier<AiChatState, AiChatState>,
              AiChatState,
              Object?,
              Object?
            >;
    element.handleCreate(ref, build);
  }
}
