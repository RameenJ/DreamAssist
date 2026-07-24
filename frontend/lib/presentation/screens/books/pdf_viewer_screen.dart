import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:pdfx/pdfx.dart';
import 'package:dio/dio.dart';

import '../../../data/services/book_api_service.dart';
import '../../../core/providers/app_providers.dart';

class PdfViewerScreen extends ConsumerStatefulWidget {
  final String bookId;
  final String bookTitle;

  const PdfViewerScreen({
    super.key,
    required this.bookId,
    required this.bookTitle,
  });

  @override
  ConsumerState<PdfViewerScreen> createState() => _PdfViewerScreenState();
}

class _PdfViewerScreenState extends ConsumerState<PdfViewerScreen> {
  PdfControllerPinch? _pdfController;
  bool _isLoading = true;
  String? _error;
  int _currentPage = 1;
  int _totalPages = 0;

  @override
  void initState() {
    super.initState();
    _loadPdf();
  }

  Future<void> _loadPdf() async {
    try {
      setState(() {
        _isLoading = true;
        _error = null;
      });

      final dioClient = ref.read(dioClientProvider);
      final token = await dioClient.getAuthToken();

      if (token == null) {
        throw Exception('Not authenticated - auth token is null');
      }

      final bookService = BookApiService(dioClient);
      final pdfUrl = bookService.getBookPdfUrl(widget.bookId);

      print('📄 [PDF INIT] Book ID: ${widget.bookId}');
      print('📄 [PDF INIT] PDF URL: $pdfUrl');
      print('📄 [PDF INIT] Token length: ${token.length}');

      final pdfData = await _fetchPdfData(pdfUrl, token);

      if (!mounted) {
        print('📄 [PDF INIT] ⚠️ Widget not mounted after fetch');
        return;
      }

      print('📄 [PDF INIT] Opening document...');
      final document = await PdfDocument.openData(pdfData);

      if (!mounted) {
        print('📄 [PDF INIT] ⚠️ Widget not mounted after document open');
        return;
      }

      final controller = PdfControllerPinch(
        document: Future.value(document),
      );

      setState(() {
        _pdfController = controller;
        _totalPages = document.pagesCount;
        _isLoading = false;
      });

      _pdfController?.addListener(_onPageChanged);
      print('📄 [PDF INIT] ✅ PDF loaded successfully with $_totalPages pages');
    } catch (e) {
      if (!mounted) return;

      setState(() {
        _error = 'Failed to load PDF: ${e.toString()}';
        _isLoading = false;
      });
      print('📄 [PDF INIT] ❌ Error: $e');
    }
  }

  Future<Uint8List> _fetchPdfData(String url, String token) async {
    try {
      final dioClient = ref.read(dioClientProvider);

      print('📄 [PDF] Fetching from URL: $url');
      print('📄 [PDF] Auth Token exists: ${token.isNotEmpty}');

      final response = await dioClient.dio.get<List<int>>(
        url,
        options: Options(
          responseType: ResponseType.bytes,
          headers: {
            'Authorization': 'Bearer $token',
          },
        ),
      );

      print('📄 [PDF] Status Code: ${response.statusCode}');
      print('📄 [PDF] Data received: ${response.data?.length ?? 0} bytes');

      if (response.data == null || response.data!.isEmpty) {
        throw Exception('No PDF data received from server (${response.statusCode})');
      }

      print('📄 [PDF] ✅ PDF fetched successfully (${response.data!.length} bytes)');
      return Uint8List.fromList(response.data!);
    } on DioException catch (e) {
      print('📄 [PDF] ❌ DioException: ${e.type}');
      print('📄 [PDF] Message: ${e.message}');
      print('📄 [PDF] Response Status: ${e.response?.statusCode}');
      print('📄 [PDF] Response Data: ${e.response?.data}');
      
      String errorMsg = 'Failed to fetch PDF: ';
      if (e.response?.statusCode == 404) {
        errorMsg += 'PDF not found (404). Book may not exist or PDF not uploaded.';
      } else if (e.response?.statusCode == 401 || e.response?.statusCode == 403) {
        errorMsg += 'Access denied (${e.response?.statusCode}). Please login again.';
      } else if (e.type == DioExceptionType.connectionTimeout) {
        errorMsg += 'Connection timeout. Please check your internet connection.';
      } else {
        errorMsg += '${e.message}';
      }
      throw Exception(errorMsg);
    } catch (e) {
      print('📄 [PDF] ❌ Unexpected Error: $e');
      throw Exception('Failed to fetch PDF: $e');
    }
  }

  void _onPageChanged() {
    if (_pdfController != null && mounted) {
      setState(() {
        _currentPage = _pdfController!.page;
      });
    }
  }

  @override
  void dispose() {
    _pdfController?.removeListener(_onPageChanged);
    _pdfController?.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              widget.bookTitle,
              style: const TextStyle(fontSize: 16),
              overflow: TextOverflow.ellipsis,
            ),
            if (!_isLoading && _totalPages > 0)
              Text(
                'Page $_currentPage of $_totalPages',
                style: const TextStyle(
                  fontSize: 12,
                  fontWeight: FontWeight.normal,
                ),
              ),
          ],
        ),
      ),
      body: _buildBody(),
    );
  }

  Widget _buildBody() {
    if (_isLoading) {
      return const Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            CircularProgressIndicator(),
            SizedBox(height: 16),
            Text('Loading PDF...'),
          ],
        ),
      );
    }

    if (_error != null) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(16.0),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(
                Icons.error_outline,
                color: Colors.red,
                size: 64,
              ),
              const SizedBox(height: 16),
              Text(
                _error!,
                textAlign: TextAlign.center,
                style: const TextStyle(fontSize: 16),
              ),
              const SizedBox(height: 24),
              ElevatedButton.icon(
                onPressed: _loadPdf,
                icon: const Icon(Icons.refresh),
                label: const Text('Retry'),
              ),
            ],
          ),
        ),
      );
    }

    if (_pdfController == null) {
      return const Center(
        child: Text('Unable to display PDF'),
      );
    }

    return PdfViewPinch(
      controller: _pdfController!,
      padding: 8,
      backgroundDecoration: const BoxDecoration(
        color: Colors.grey,
      ),
    );
  }
}