// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'category_provider.dart';

// **************************************************************************
// RiverpodGenerator
// **************************************************************************

// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, type=warning
/// Category state notifier

@ProviderFor(Category)
final categoryProvider = CategoryProvider._();

/// Category state notifier
final class CategoryProvider
    extends $NotifierProvider<Category, CategoryState> {
  /// Category state notifier
  CategoryProvider._()
    : super(
        from: null,
        argument: null,
        retry: null,
        name: r'categoryProvider',
        isAutoDispose: true,
        dependencies: null,
        $allTransitiveDependencies: null,
      );

  @override
  String debugGetCreateSourceHash() => _$categoryHash();

  @$internal
  @override
  Category create() => Category();

  /// {@macro riverpod.override_with_value}
  Override overrideWithValue(CategoryState value) {
    return $ProviderOverride(
      origin: this,
      providerOverride: $SyncValueProvider<CategoryState>(value),
    );
  }
}

String _$categoryHash() => r'46c828c6586a162b52b4fa1007f7485a8dbfb995';

/// Category state notifier

abstract class _$Category extends $Notifier<CategoryState> {
  CategoryState build();
  @$mustCallSuper
  @override
  void runBuild() {
    final ref = this.ref as $Ref<CategoryState, CategoryState>;
    final element =
        ref.element
            as $ClassProviderElement<
              AnyNotifier<CategoryState, CategoryState>,
              CategoryState,
              Object?,
              Object?
            >;
    element.handleCreate(ref, build);
  }
}
