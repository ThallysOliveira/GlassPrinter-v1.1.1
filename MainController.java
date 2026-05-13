package com.autoglass.glassprinter.controller;

import javafx.fxml.FXML;
import javafx.scene.layout.VBox;
import javafx.animation.TranslateTransition;
import javafx.util.Duration;
import javafx.scene.control.Button;
import javafx.scene.layout.AnchorPane;

/**
 * Controller principal do GlassPrinter em JavaFX.
 * Gerencia o comportamento responsivo do menu lateral (Activity Bar).
 */
public class MainController {

    @FXML private VBox sidebar;
    @FXML private AnchorPane mainContent;
    
    private static final double EXPANDED_WIDTH = 220.0;
    private static final double COLLAPSED_WIDTH = 60.0;

    @FXML
    public void initialize() {
        // Configura o comportamento de Hover (VS Code Style)
        sidebar.setOnMouseEntered(e -> animateSidebar(EXPANDED_WIDTH));
        sidebar.setOnMouseExited(e -> animateSidebar(COLLAPSED_WIDTH));
    }

    /**
     * Anima a expansão/contração da sidebar com suavidade.
     */
    private void animateSidebar(double targetWidth) {
        // Em JavaFX, podemos animar propriedades diretamente
        // Para um deploy profissional, usamos Timeline ou Transitions
        sidebar.setPrefWidth(targetWidth);
        
        // Gerencia a visibilidade dos textos dos botões via CSS ou Logic
        if (targetWidth == COLLAPSED_WIDTH) {
            sidebar.getStyleClass().add("collapsed");
        } else {
            sidebar.getStyleClass().remove("collapsed");
        }
    }

    @FXML
    private void handleGenerateLabels() {
        // Chamada para o Service de PDF (Ex: Apache PDFBox)
        System.out.println("Gerando etiquetas via Java Engine...");
    }
}