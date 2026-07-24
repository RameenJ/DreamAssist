// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'book_provider.dart';

// **************************************************************************
// RiverpodGenerator
// **************************************************************************

// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, type=warning
/// Book state notifier

@ProviderFor(Book)
final bookProvider = BookProvider._();

/// Book state notifier
final class BookProvider extends $NotifierProvider<Book, BookState> {
  /// Book state notifier
  BookProvider._()
    : super(
        from: null,
        argument: null,
        retry: null,
        name: r'bookProvider',
        isAutoDispose: true,
        dependencies: null,
        $allTransitiveDependencies: null,
      );

  @override
  String debugGetCreateSourceHash() => _$bookHash();

  @$internal
  @override
  Book create() => Book();

  /// {@macro riverpod.override_with_value}
  Override overrideWithValue(BookState value) {
    return $ProviderOverride(
      origin: this,
      providerOverride: $SyncValueProvider<BookState>(value),
    );
  }
}

String _$bookHash() => r'50e41a9a98d17e51b19481976e8aa018f02014ae';

/// Book state notifier

abstract class _$Book extends $Notifier<BookState> {
  BookState build();
  @$mustCallSuper
  @override
  void runBuild() {
    final ref = this.ref as $Ref<BookState, BookState>;
    final element =
        ref.element
            as $ClassProviderElement<
              AnyNotifier<BookState, BookState>,
              BookState,
              Object?,
              Object?
            >;
    element.handleCreate(ref, build);
  }
}

/// Provider for a specific book's details

@ProviderFor(bookDetail)
final bookDetailProvider = BookDetailFamily._();

/// Provider for a specific book's details

final class BookDetailProvider
    extends
        $FunctionalProvider<
          AsyncValue<BookModel>,
          BookModel,
          FutureOr<BookModel>
        >
    with $FutureModifier<BookModel>, $FutureProvider<BookModel> {
  /// Provider for a specific book's details
  BookDetailProvider._({
    required BookDetailFamily super.from,
    required String super.argument,
  }) : super(
         retry: null,
         name: r'bookDetailProvider',
         isAutoDispose: true,
         dependencies: null,
         $allTransitiveDependencies: null,
       );

  @override
  String debugGetCreateSourceHash() => _$bookDetailHash();

  @override
  String toString() {
    return r'bookDetailProvider'
        ''
        '($argument)';
  }

  @$internal
  @override
  $FutureProviderElement<BookModel> $createElement($ProviderPointer pointer) =>
      $FutureProviderElement(pointer);

  @override
  FutureOr<BookModel> create(Ref ref) {
    final argument = this.argument as String;
    return bookDetail(ref, argument);
  }

  @override
  bool operator ==(Object other) {
    return other is BookDetailProvider && other.argument == argument;
  }

  @override
  int get hashCode {
    return argument.hashCode;
  }
}

String _$bookDetailHash() => r'6d0f79be5d6d317a5018b17852b786ff51a8469d';

/// Provider for a specific book's details

final class BookDetailFamily extends $Family
    with $FunctionalFamilyOverride<FutureOr<BookModel>, String> {
  BookDetailFamily._()
    : super(
        retry: null,
        name: r'bookDetailProvider',
        dependencies: null,
        $allTransitiveDependencies: null,
        isAutoDispose: true,
      );

  /// Provider for a specific book's details

  BookDetailProvider call(String bookId) =>
      BookDetailProvider._(argument: bookId, from: this);

  @override
  String toString() => r'bookDetailProvider';
}

/// Provider for fetching topics of a specific book

@ProviderFor(bookTopics)
final bookTopicsProvider = BookTopicsFamily._();

/// Provider for fetching topics of a specific book

final class BookTopicsProvider
    extends
        $FunctionalProvider<
          AsyncValue<List<BookTopicModel>>,
          List<BookTopicModel>,
          FutureOr<List<BookTopicModel>>
        >
    with
        $FutureModifier<List<BookTopicModel>>,
        $FutureProvider<List<BookTopicModel>> {
  /// Provider for fetching topics of a specific book
  BookTopicsProvider._({
    required BookTopicsFamily super.from,
    required String super.argument,
  }) : super(
         retry: null,
         name: r'bookTopicsProvider',
         isAutoDispose: true,
         dependencies: null,
         $allTransitiveDependencies: null,
       );

  @override
  String debugGetCreateSourceHash() => _$bookTopicsHash();

  @override
  String toString() {
    return r'bookTopicsProvider'
        ''
        '($argument)';
  }

  @$internal
  @override
  $FutureProviderElement<List<BookTopicModel>> $createElement(
    $ProviderPointer pointer,
  ) => $FutureProviderElement(pointer);

  @override
  FutureOr<List<BookTopicModel>> create(Ref ref) {
    final argument = this.argument as String;
    return bookTopics(ref, argument);
  }

  @override
  bool operator ==(Object other) {
    return other is BookTopicsProvider && other.argument == argument;
  }

  @override
  int get hashCode {
    return argument.hashCode;
  }
}

String _$bookTopicsHash() => r'700dbb8bfdd5f99916a496bee2f7bdeb7988138f';

/// Provider for fetching topics of a specific book

final class BookTopicsFamily extends $Family
    with $FunctionalFamilyOverride<FutureOr<List<BookTopicModel>>, String> {
  BookTopicsFamily._()
    : super(
        retry: null,
        name: r'bookTopicsProvider',
        dependencies: null,
        $allTransitiveDependencies: null,
        isAutoDispose: true,
      );

  /// Provider for fetching topics of a specific book

  BookTopicsProvider call(String bookId) =>
      BookTopicsProvider._(argument: bookId, from: this);

  @override
  String toString() => r'bookTopicsProvider';
}
