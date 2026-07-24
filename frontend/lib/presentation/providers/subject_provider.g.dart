// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'subject_provider.dart';

// **************************************************************************
// RiverpodGenerator
// **************************************************************************

// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, type=warning
/// Subject state notifier

@ProviderFor(Subject)
final subjectProvider = SubjectProvider._();

/// Subject state notifier
final class SubjectProvider extends $NotifierProvider<Subject, SubjectState> {
  /// Subject state notifier
  SubjectProvider._()
    : super(
        from: null,
        argument: null,
        retry: null,
        name: r'subjectProvider',
        isAutoDispose: true,
        dependencies: null,
        $allTransitiveDependencies: null,
      );

  @override
  String debugGetCreateSourceHash() => _$subjectHash();

  @$internal
  @override
  Subject create() => Subject();

  /// {@macro riverpod.override_with_value}
  Override overrideWithValue(SubjectState value) {
    return $ProviderOverride(
      origin: this,
      providerOverride: $SyncValueProvider<SubjectState>(value),
    );
  }
}

String _$subjectHash() => r'2945de3f15208715bedb52460d3ba6e6680ee421';

/// Subject state notifier

abstract class _$Subject extends $Notifier<SubjectState> {
  SubjectState build();
  @$mustCallSuper
  @override
  void runBuild() {
    final ref = this.ref as $Ref<SubjectState, SubjectState>;
    final element =
        ref.element
            as $ClassProviderElement<
              AnyNotifier<SubjectState, SubjectState>,
              SubjectState,
              Object?,
              Object?
            >;
    element.handleCreate(ref, build);
  }
}
