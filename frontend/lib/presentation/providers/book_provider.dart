import 'package:riverpod_annotation/riverpod_annotation.dart';
import '../../data/models/book_model.dart';
import '../../data/services/book_api_service.dart';
import '../../core/providers/app_providers.dart';

part 'book_provider.g.dart';

/// Book state
class BookState {
  final List<BookModel> books;
  final bool isLoading;
  final String? error;

  const BookState({
    this.books = const [],
    this.isLoading = false,
    this.error,
  });

  BookState copyWith({
    List<BookModel>? books,
    bool? isLoading,
    String? error,
  }) {
    return BookState(
      books: books ?? this.books,
      isLoading: isLoading ?? this.isLoading,
      error: error,
    );
  }
}

/// Book state notifier
@riverpod
class Book extends _$Book {
  @override
  BookState build() {
    return const BookState();
  }

  BookApiService get _bookService => ref.watch(bookApiServiceProvider);

  /// Fetch all books
  Future<void> fetchBooks() async {
    state = state.copyWith(isLoading: true, error: null);

    final result = await _bookService.getUserBooks();
    result.when(
      success: (books) {
        state = state.copyWith(books: books, isLoading: false);
      },
      failure: (message) {
        state = state.copyWith(isLoading: false, error: message);
      },
    );
  }

  /// Upload a new book
  Future<bool> uploadBook({
    required String filePath,
    String? title,
    String? categoryId,
    String? subject,
    Function(int, int)? onProgress,
  }) async {
    state = state.copyWith(isLoading: true, error: null);

    final result = await _bookService.uploadBook(
      filePath: filePath,
      title: title,
      categoryId: categoryId,
      subject: subject,
      onProgress: onProgress,
    );

    return result.when(
      success: (book) {
        // Add new book to the list
        state = state.copyWith(
          books: [...state.books, book],
          isLoading: false,
        );
        return true;
      },
      failure: (message) {
        state = state.copyWith(isLoading: false, error: message);
        return false;
      },
    );
  }

  /// Delete a book
  Future<bool> deleteBook(String bookId) async {
    state = state.copyWith(isLoading: true, error: null);

    final result = await _bookService.deleteBook(bookId);

    return result.when(
      success: (_) {
        // Remove the book from the list
        final updatedBooks = state.books.where((book) => book.id != bookId).toList();
        state = state.copyWith(books: updatedBooks, isLoading: false);
        return true;
      },
      failure: (message) {
        state = state.copyWith(isLoading: false, error: message);
        return false;
      },
    );
  }

  /// Update book category
  Future<bool> updateBookCategory(String bookId, String? categoryId) async {
    final result = await _bookService.updateBookCategory(bookId, categoryId);

    return result.when(
      success: (updatedBook) {
        // Update the book in the list
        final updatedBooks = state.books.map((book) {
          return book.id == bookId ? updatedBook : book;
        }).toList();
        state = state.copyWith(books: updatedBooks);
        return true;
      },
      failure: (message) {
        state = state.copyWith(error: message);
        return false;
      },
    );
  }

  /// Get book by ID from state
  BookModel? getBookById(String bookId) {
    try {
      return state.books.firstWhere((book) => book.id == bookId);
    } catch (e) {
      return null;
    }
  }

  /// Clear error
  void clearError() {
    state = state.copyWith(error: null);
  }
}

/// Provider for a specific book's details
@riverpod
Future<BookModel> bookDetail(Ref ref, String bookId) async {
  final bookService = ref.watch(bookApiServiceProvider);
  final result = await bookService.getBookById(bookId);
  
  return result.when(
    success: (book) => book,
    failure: (error) => throw Exception(error),
  );
}

/// Provider for fetching topics of a specific book
@riverpod
Future<List<BookTopicModel>> bookTopics(Ref ref, String bookId) async {
  final bookService = ref.watch(bookApiServiceProvider);
  final result = await bookService.getBookTopics(bookId);
  
  return result.when(
    success: (topics) => topics,
    failure: (error) => throw Exception(error),
  );
}
