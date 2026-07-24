// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'diagnostic_provider.dart';

// **************************************************************************
// RiverpodGenerator
// **************************************************************************

// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, type=warning
/// Diagnostic quiz state notifier

@ProviderFor(Diagnostic)
final diagnosticProvider = DiagnosticProvider._();

/// Diagnostic quiz state notifier
final class DiagnosticProvider
    extends $NotifierProvider<Diagnostic, DiagnosticState> {
  /// Diagnostic quiz state notifier
  DiagnosticProvider._()
    : super(
        from: null,
        argument: null,
        retry: null,
        name: r'diagnosticProvider',
        isAutoDispose: true,
        dependencies: null,
        $allTransitiveDependencies: null,
      );

  @override
  String debugGetCreateSourceHash() => _$diagnosticHash();

  @$internal
  @override
  Diagnostic create() => Diagnostic();

  /// {@macro riverpod.override_with_value}
  Override overrideWithValue(DiagnosticState value) {
    return $ProviderOverride(
      origin: this,
      providerOverride: $SyncValueProvider<DiagnosticState>(value),
    );
  }
}

String _$diagnosticHash() => r'5854d052aad07876047d9b3638d9e6b5ba5e0215';

/// Diagnostic quiz state notifier

abstract class _$Diagnostic extends $Notifier<DiagnosticState> {
  DiagnosticState build();
  @$mustCallSuper
  @override
  void runBuild() {
    final ref = this.ref as $Ref<DiagnosticState, DiagnosticState>;
    final element =
        ref.element
            as $ClassProviderElement<
              AnyNotifier<DiagnosticState, DiagnosticState>,
              DiagnosticState,
              Object?,
              Object?
            >;
    element.handleCreate(ref, build);
  }
}
